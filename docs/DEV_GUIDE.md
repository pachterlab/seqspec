---
title: Development & Release Guide
date: 2025-06-13
authors:
  - name: A. Sina Booeshaghi
---

## Development Workflow

1. **Normal Development**
   ```bash
   # Always work in devel branch
   git add .
   git commit -m "your changes"
   git push origin devel
   ```

2. **Creating a Release**
   ```bash
   # 1. Create a Pull Request on GitHub
   # - Go to GitHub repository
   # - Create PR from devel to main
   # - Add description of changes
   # - Wait for review and approval
   # - Merge PR to main

   # 2. Update local main branch
   git checkout main
   git pull origin main

   # 3. Create the release
   make release
   # This will:
   # - Prompt for version number
   # - Create git tag
   # - Push tag to GitHub
   # - Build package
   # - Upload to PyPI

   # 4. Return to development
   git checkout devel
   ```

## Version Numbering

Follow semantic versioning:
- `0.3.1` → `0.3.2` for bug fixes (patch)
- `0.3.1` → `0.4.0` for new features (minor)
- `0.3.1` → `1.0.0` for breaking changes (major)

## Important Notes

1. **Never manually edit `__init__.py`**
   - Version is managed through git tags
   - `__init__.py` is updated automatically

2. **Always release from `main` branch**
   - Ensures PyPI version matches main branch
   - Git tags point to correct code
   - Release process is clean and reproducible

3. **Development versions**
   - During development: `0.3.1.dev123+gabc123`
   - After release: `0.3.2`
   - Handled automatically by setuptools_scm

## Using uv for Development

### Setting up a Development Environment

1. **Create a new environment**
   ```bash
   # Create a new environment
   uv venv .venv
   
   # Activate the environment
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv/Scripts/activate  # On Windows
   ```

2. **Install Dependencies**
   ```bash
   # Install runtime dependencies
   uv pip install .
   
   # Install development dependencies
   uv pip install ".[dev]"
   ```

### Using uv for Package Management

1. **Installing seqspec**
   ```bash
   # Install latest release
   uv pip install seqspec
   
   # Install specific version
   uv pip install seqspec==0.3.1
   
   # Install from git
   uv pip install git+https://github.com/sbooeshaghi/seqspec.git
   ```

2. **Development Workflow with uv**
   ```bash
   # Create new environment for testing
   uv venv test-env
   source test-env/bin/activate
   
   # Install all dependencies
   uv pip install ".[dev]"
   
   # Run tests
   pytest
   ```

### Best Practices with uv

1. **Environment Management**
   - Use separate environments for different projects
   - Keep development environment separate from system Python
   - Use `uv venv` to create isolated environments

2. **Dependency Management**
   - Runtime dependencies are in `pyproject.toml` under `[project]`
   - Development dependencies are under `[project.optional-dependencies]`
   - Install with `uv pip install ".[dev]"` for development
   - Install with `uv pip install .` for runtime only

3. **Testing with uv**
   ```bash
   # Create test environment
   uv venv test-env
   source test-env/bin/activate
   
   # Install all dependencies
   uv pip install ".[dev]"
   
   # Run tests
   pytest
   ```

4. **Building with uv**
   ```bash
   # Install build dependencies
   uv pip install ".[dev]"
   
   # Build package
   make build
   ```

## Troubleshooting

### Release Issues

If `make release` fails:
1. Ensure you're on `main` branch
2. Ensure `main` is up to date (`git pull origin main`)
3. Check PyPI credentials are correct
4. Check git tags are being pushed correctly

### uv Issues

1. **Common Issues**
   - If `uv pip install` fails, try `--no-deps` flag
   - If environment activation fails, check path
   - If package not found, check PyPI index

2. **Updating uv**
   ```bash
   # Update uv itself
   uv pip install --upgrade uv
   ```

3. **Cleaning up**
   ```bash
   # Remove old environments
   rm -rf .venv test-env
   
   # Clear uv cache
   uv cache clean
   ```

## Common Commands

```bash
# Check current version
make version

# Build package without releasing
make build

# Clean build artifacts
make clean
```

## Dependencies

All dependencies are managed in `pyproject.toml`:
- Runtime dependencies under `[project]`
- Development dependencies under `[project.optional-dependencies]`

No separate `requirements.txt` or `dev-requirements.txt` files are needed.