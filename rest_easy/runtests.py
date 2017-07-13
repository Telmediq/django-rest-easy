# coding: utf-8
# pylint: skip-file
"""
Tests for django-rest-easy. So far not ported from proprietary code.
"""
from __future__ import unicode_literals

import os
import sys

from django.conf import settings
import django


if __name__ == '__main__':
    settings.configure(DEBUG_PROPAGATE_EXCEPTIONS=True,
                       DATABASES={
                           'default': {
                               'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'
                           }
                       },
                       SITE_ID=1,
                       SECRET_KEY='not very secret in tests',
                       USE_I18N=True,
                       USE_L10N=True,
                       STATIC_URL='/static/',
                       TEMPLATES=[
                           {
                               'BACKEND': 'django.template.backends.django.DjangoTemplates',
                               'APP_DIRS': True,
                           },
                       ],
                       MIDDLEWARE_CLASSES=(
                           'django.middleware.common.CommonMiddleware',
                           'django.contrib.sessions.middleware.SessionMiddleware',
                           'django.contrib.auth.middleware.AuthenticationMiddleware',
                           'django.contrib.messages.middleware.MessageMiddleware',
                       ),
                       INSTALLED_APPS=(
                           'django.contrib.auth',
                           'django.contrib.contenttypes',
                           'django.contrib.sessions',
                           'django.contrib.sites',
                           'django.contrib.staticfiles',
                           'rest_framework',
                           'rest_easy',
                           'rest_easy.tests'
                       ),
                       PASSWORD_HASHERS=(
                           'django.contrib.auth.hashers.MD5PasswordHasher',
                       ),
                       REST_EASY_VIEW_BASES=['rest_easy.tests.mixins.EmptyBase'],
                       REST_EASY_GENERIC_VIEW_MIXINS=['rest_easy.tests.mixins.EmptyMixin'])
    django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    from django.test.runner import DiscoverRunner

    runner_class = DiscoverRunner
    test_args = ['tests']

    failures = runner_class(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)
