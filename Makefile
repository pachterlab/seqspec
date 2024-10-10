.PHONY : clean build upload bump_patch bump_minor bump_major push_release tag_release release_patch release_minor release_major

clean:
	rm -rf build
	rm -rf dist
	rm -rf seqspec.egg-info
	rm -rf docs/_build
	rm -rf docs/api
	rm -rf .coverage

bump_patch:
	bumpversion patch

bump_minor:
	bumpversion minor

bump_major:
	bumpversion major

push_release:
	git push && git push --tags

# Tag the release with the current version from bumpversion
tag_release:
	git tag -a "v$$(python setup.py --version)" -m "Release v$$(python setup.py --version)"

# Build both the source distribution and wheel distribution
build: sdist wheel

# Build the source distribution
sdist:
	python setup.py sdist

# Build the wheel distribution
wheel:
	python -m build --wheel

# Upload both sdist and wheel to PyPI using twine
upload: 
	twine upload dist/*

# Combined commands for different types of releases

# Release a patch version: bump patch, build, tag, push, and upload
release_patch: clean bump_patch build tag_release push_release upload

# Release a minor version: bump minor, build, tag, push, and upload
release_minor: clean bump_minor build tag_release push_release upload

# Release a major version: bump major, build, tag, push, and upload
release_major: clean bump_major build tag_release push_release upload
