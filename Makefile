.PHONY : clean build upload release

clean:
	rm -rf build
	rm -rf dist
	rm -rf seqspec.egg-info
	rm -rf docs/_build
	rm -rf docs/api
	rm -rf .coverage

# Build both the source distribution and wheel distribution
build:
	python -m build

# Upload both sdist and wheel to PyPI using twine
upload: 
	twine upload dist/*

# Get current version
version:
	@python -c "import setuptools_scm; print(setuptools_scm.get_version())"

# Create a new release
release:
	@read -p "Enter version (e.g., 0.3.2): " version; \
	git tag -a "v$$version" -m "Release v$$version"; \
	git push && git push --tags; \
	make clean build upload
