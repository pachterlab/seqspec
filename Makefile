.PHONY : clean build upload release

 

clean:
	rm -rf build
	rm -rf dist
	rm -rf seqspec.egg-info
	rm -rf seqspec.egg_info
	rm -rf docs/_build
	rm -rf docs/api
	rm -rf .coverage
	rm -rf _build

# Build both the source distribution and wheel distribution
build:
	uv run python -m build

# Upload both sdist and wheel to PyPI using twine
upload: 
	uvx twine upload dist/*

# Get current version
version:
	@uv run python -c "import tomllib, pathlib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_bytes().decode()).get('project',{}).get('version','unknown'))"

# Create a new release
release:
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then echo "Switch to main before releasing"; exit 1; fi
	@if [ -n "$$(git status --porcelain)" ]; then echo "Working tree not clean"; git status; exit 1; fi
	@git pull --ff-only
	@version=$$(uv run python -c "import tomllib, pathlib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_bytes().decode())['project']['version'])"); \
	uv run pytest || { echo "Tests failed"; exit 1; }; \
	git tag -a "v$$version" -m "Release v$$version"; \
	git push origin main && git push origin --tags; \
	make clean build upload
