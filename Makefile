test:
	@tox -e py27-1.5.x

test_all:
	tox

upload:
	@python setup.py sdist upload
