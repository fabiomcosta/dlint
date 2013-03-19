test:
	@nosetests --with-coverage ./tests/ -s --cover-package=dlint

test_setup:
	@pip install -r test_requirements.txt

upload:
	@python setup.py sdist upload
