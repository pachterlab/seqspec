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
	@uv run python -c "import setuptools_scm; print(setuptools_scm.get_version())"

# Create a new release
release:
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then echo "Switch to main before releasing"; exit 1; fi
	@if [ -n "$$(git status --porcelain)" ]; then echo "Working tree not clean"; git status; exit 1; fi
	@git pull --ff-only
	@uv run pytest || { echo "Tests failed"; exit 1; }
	@read -p "Enter version (e.g., 0.3.2): " version; \
	git tag -a "v$$version" -m "Release v$$version"; \
	git push origin main && git push origin --tags; \
	make clean build upload
