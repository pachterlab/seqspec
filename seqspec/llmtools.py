from functools import wraps
from typing import Callable, List, Type

from pydantic import BaseModel, ValidationError

# ----------------------------
# LLMInput base model
# ----------------------------


class LLMInput(BaseModel):
    def validate_required(self, required_fields: List[str]) -> List[str]:
        """Return list of required fields that are None or empty string."""
        return [f for f in required_fields if getattr(self, f, None) in [None, ""]]

    def has_all_required(self, required_fields: List[str]) -> bool:
        return not self.validate_required(required_fields)

    def missing_prompt(self, required_fields: List[str]) -> str:
        """Return a human-readable message for missing fields."""
        missing = self.validate_required(required_fields)
        if not missing:
            return ""
        hints = [f"• {f.replace('_', ' ')}" for f in missing]
        return "Missing required fields:\n" + "\n".join(hints)


# ----------------------------
# Pydantic validation wrapper
# ----------------------------


def validate_with_pydantic(
    model_class: Type[BaseModel], required_fields: List[str] = []
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                params_obj = model_class(**kwargs)

                # Optional custom field-level validation
                if required_fields and hasattr(params_obj, "validate_required"):
                    missing = params_obj.validate_required(required_fields)  # type: ignore
                    if missing:
                        return {
                            "status": "insufficient_data",
                            "missing_params": missing,
                            "tool_name": func.__name__,
                            "message": f"Missing required parameters: {', '.join(missing)}",
                        }

                return await func(params_obj)

            except ValidationError as e:
                errors = e.errors()
                missing = [
                    err["loc"][0]
                    for err in errors
                    if err["type"] == "value_error.missing"
                ]
                if missing:
                    return {
                        "status": "insufficient_data",
                        "missing_params": missing,
                        "tool_name": func.__name__,
                        "message": f"Missing required parameters: {', '.join(missing)}",  # type: ignore
                    }
                return {
                    "status": "validation_failed",
                    "errors": [f"{err['loc'][0]}: {err['msg']}" for err in errors],
                    "tool_name": func.__name__,
                }

            except Exception as e:
                return {
                    "status": "error",
                    "tool_name": func.__name__,
                    "message": str(e),
                }

        return wrapper

    return decorator
