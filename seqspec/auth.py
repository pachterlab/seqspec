import json
import os
import tomllib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

AUTH_CONFIG_ENV = "SEQSPEC_AUTH_CONFIG"


class AuthProfile:
    def __init__(
        self, hosts: List[str], kind: str, username_env: str, password_env: str
    ) -> None:
        self.hosts = hosts
        self.kind = kind
        self.username_env = username_env
        self.password_env = password_env

    @classmethod
    def from_dict(cls, data: Dict) -> "AuthProfile":
        return cls(
            hosts=list(data.get("hosts", [])),
            kind=str(data.get("kind", "basic")),
            username_env=str(data["username_env"]),
            password_env=str(data["password_env"]),
        )

    def to_dict(self) -> Dict:
        return {
            "hosts": self.hosts,
            "kind": self.kind,
            "username_env": self.username_env,
            "password_env": self.password_env,
        }

    def matches_host(self, host: str) -> bool:
        return any(candidate.lower() == host.lower() for candidate in self.hosts)


class AuthRegistry:
    def __init__(self, location: Dict, profiles: Dict[str, AuthProfile]) -> None:
        self.location = location
        self.profiles = profiles

    @classmethod
    def load(cls) -> "AuthRegistry":
        location = config_location()
        profiles = load_profiles(location)
        return cls(location, profiles)

    def profile_summaries(self) -> List[Dict]:
        summaries = []
        for name, profile in self.profiles.items():
            summaries.append(
                {
                    "name": name,
                    "kind": profile.kind,
                    "hosts": profile.hosts,
                    "username_env": profile.username_env,
                    "username_present": os.environ.get(profile.username_env) is not None,
                    "password_env": profile.password_env,
                    "password_present": os.environ.get(profile.password_env) is not None,
                }
            )
        return summaries

    def resolve_summary(
        self, url: str, selected_profile: Optional[str] = None
    ) -> Dict[str, object]:
        host = host_from_url(url)
        resolved = self.resolve_profile(host, selected_profile)
        profile = None
        if resolved is not None:
            name, match = resolved
            profile = {
                "name": name,
                "kind": match.kind,
                "hosts": match.hosts,
                "username_env": match.username_env,
                "username_present": os.environ.get(match.username_env) is not None,
                "password_env": match.password_env,
                "password_present": os.environ.get(match.password_env) is not None,
            }
        return {"url": url, "host": host, "profile": profile}

    def resolve_profile(
        self, host: str, selected_profile: Optional[str] = None
    ) -> Optional[Tuple[str, AuthProfile]]:
        if selected_profile is not None:
            if selected_profile not in self.profiles:
                raise ValueError(
                    f"auth profile '{selected_profile}' is not defined in {display_config_path(self.location)}"
                )
            profile = self.profiles[selected_profile]
            if not profile.matches_host(host):
                raise ValueError(
                    f"auth profile '{selected_profile}' does not match host '{host}'"
                )
            return (selected_profile, profile)

        matches = [
            (name, profile)
            for name, profile in self.profiles.items()
            if profile.matches_host(host)
        ]
        if len(matches) > 1:
            names = ", ".join(name for name, _ in matches)
            raise ValueError(f"multiple auth profiles match host '{host}': {names}")
        if len(matches) == 1:
            return matches[0]
        return None

    def resolve_requests_auth(
        self, url: str, selected_profile: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        host = host_from_url(url)
        resolved = self.resolve_profile(host, selected_profile)
        if resolved is None:
            return None
        profile_name, profile = resolved
        username = os.environ.get(profile.username_env)
        if username is None:
            raise ValueError(
                f"auth profile '{profile_name}' requires env var '{profile.username_env}' for host '{host}'"
            )
        password = os.environ.get(profile.password_env)
        if password is None:
            raise ValueError(
                f"auth profile '{profile_name}' requires env var '{profile.password_env}' for host '{host}'"
            )
        return (username, password)


def config_location() -> Dict[str, object]:
    env_path = os.environ.get(AUTH_CONFIG_ENV)
    if env_path:
        path = Path(env_path)
        return {
            "path": path,
            "source": f"env:{AUTH_CONFIG_ENV}",
            "exists": path.exists(),
        }

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        path = Path(xdg) / "seqspec" / "auth.toml"
        return {"path": path, "source": "xdg_config_home", "exists": path.exists()}

    home = os.environ.get("HOME")
    if home:
        path = Path(home) / ".config" / "seqspec" / "auth.toml"
        return {"path": path, "source": "home_default", "exists": path.exists()}

    return {"path": None, "source": "unavailable", "exists": False}


def load_profiles(location: Dict[str, object]) -> Dict[str, AuthProfile]:
    path = location.get("path")
    if path is None:
        return {}

    path = Path(path)
    if not path.exists():
        if str(location["source"]).startswith("env:"):
            raise ValueError(f"auth config does not exist: {path}")
        return {}

    with open(path, "rb") as stream:
        config = tomllib.load(stream)

    profiles = config.get("profiles", {})
    return {name: AuthProfile.from_dict(profile) for name, profile in profiles.items()}


def init_profile(profile_name: str, profile: AuthProfile) -> Dict[str, object]:
    location = config_location()
    path = location.get("path")
    if path is None:
        raise ValueError("no auth config path is available on this system")

    path = Path(path)
    created_config = not path.exists()
    profiles = {}
    if path.exists():
        profiles = load_profiles(location)
    updated_profile = profile_name in profiles
    profiles[profile_name] = profile

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_config(profiles))

    return {
        "profile": profile_name,
        "path": str(path),
        "created_config": created_config,
        "updated_profile": updated_profile,
        "hosts": profile.hosts,
        "kind": profile.kind,
        "username_env": profile.username_env,
        "password_env": profile.password_env,
    }


def render_config(profiles: Dict[str, AuthProfile]) -> str:
    lines: List[str] = []
    for name, profile in profiles.items():
        lines.append(f"[profiles.{name}]")
        hosts = ", ".join(json.dumps(host) for host in profile.hosts)
        lines.append(f"hosts = [{hosts}]")
        lines.append(f'kind = "{profile.kind}"')
        lines.append(f'username_env = "{profile.username_env}"')
        lines.append(f'password_env = "{profile.password_env}"')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def host_from_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        raise ValueError(f"URL '{url}' does not contain a scheme")
    if not parsed.hostname:
        raise ValueError(f"URL '{url}' has an empty host")
    return parsed.hostname.lower()


def display_config_path(location: Dict[str, object]) -> str:
    path = location.get("path")
    if path is None:
        return "<unavailable>"
    return str(path)
