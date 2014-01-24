import sys

from django.conf import settings


def main():
    settings.configure(
        ROOT_URLCONF='wsrequest.tests',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME':  'db.sqlite3',
            }
        }
    )

    from django.test.utils import get_runner

    test_runner = get_runner(settings)(verbosity=1, interactive=True)

    failures = test_runner.run_tests(['wsrequest.tests'])

    sys.exit(failures)


if __name__ == '__main__':
    main()
