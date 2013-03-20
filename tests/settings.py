
INSTALLED_APPS = (
    'django_nose',
    'tests',
    'dlint',
)

NOSE_ARGS = [
    '-s',
    '--with-coverage',
    '--cover-package=dlint',
]

TEST_RUNNER = 'django_nose.BasicNoseRunner'

# boilerplate necessary
# to a django app
SECRET_KEY = 'dlint'

import django
# just to avoid the database creating while
# executing tests on django 1.5
# thank for finaly making it possible :)
if django.get_version() < '1.5':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'TEST_NAME': ':memory:'
        }
    }
