.PHONY : clean build upload

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

build:
	python -m build --wheel

upload:
	twine upload dist/*
