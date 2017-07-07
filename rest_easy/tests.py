# coding: utf-8
# pylint: skip-file
"""
Tests for django-rest-easy. So far not ported from proprietary code.
"""
from __future__ import unicode_literals

import unittest

from django.conf import settings
from django.db import models

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
                   ROOT_URLCONF='tests.urls',
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
                   ),
                   PASSWORD_HASHERS=(
                       'django.contrib.auth.hashers.MD5PasswordHasher',
                   ))
try:
    import django
    django.setup()
except AttributeError:
    pass

from rest_easy.exceptions import RestEasyException
from rest_easy.models import deserialize_data, SerializableMixin
from rest_easy.serializers import ModelSerializer
from rest_easy.views import ModelViewSet
from rest_easy.scopes import ScopeQuerySet


class MockModel(SerializableMixin, models.Model):
    class Meta:
        app_label = 'rest_easy'

    value = models.CharField(max_length=50)


class MockModel2(SerializableMixin, models.Model):
    class Meta:
        app_label = 'rest_easy'

    value = models.CharField(max_length=50)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        pass


class TestSerializers(BaseTestCase):
    def testModelSerializerMissingFields(self):
        def inner():
            class MockSerializer(ModelSerializer):
                class Meta:
                    fields = '__all__'
                    model = MockModel

        def inner2():
            class MockSerializer(ModelSerializer):
                class Meta:
                    fields = '__all__'
                    schema = 'default'

        def inner3():
            class MockSerializer(ModelSerializer):
                class Meta:
                    fields = '__all__'

        self.assertRaises(AttributeError, inner)
        self.assertRaises(AttributeError, inner2)
        self.assertRaises(AttributeError, inner3)

    def testModelSerializerAutoFields(self):
        class MockSerializer(ModelSerializer):
            class Meta:
                fields = '__all__'
                model = MockModel
                schema = 'default'

        self.assertTrue(MockSerializer._declared_fields['model'].value == 'rest_easy.MockModel')
        self.assertTrue(MockSerializer._declared_fields['schema'].value == 'default')

    def testModelSerializerAutoFieldsNoneModel(self):
        class MockSerializer(ModelSerializer):
            class Meta:
                fields = '__all__'
                model = None
                schema = 'default'

        self.assertTrue(MockSerializer._declared_fields['model'].value is None)
        self.assertTrue(MockSerializer._declared_fields['schema'].value == 'default')


class TestModels(BaseTestCase):
    def setUp(self):
        super(TestModels, self).setUp()

        class MockSerializer(ModelSerializer):
            class Meta:
                fields = '__all__'
                model = MockModel
                schema = 'default'

        self.serializer = MockSerializer
        pass

    def test_get_serializer_success(self):
        taggable = MockModel(value='asd')
        self.assertEqual(taggable.get_serializer('default'), self.serializer)

    def test_get_serializer_failure(self):
        taggable = MockModel(value='asd')
        self.assertEqual(taggable.get_serializer('nope'), None)

    def test_serialize_success(self):
        taggable = MockModel(value='asd')
        serialized = taggable.serialize()
        self.assertEqual(serialized['model'], 'rest_easy.MockModel')
        self.assertEqual(serialized['schema'], 'default')
        self.assertEqual(serialized['value'], 'asd')

    def test_serialize_failure(self):
        taggable = MockModel(value='asd')
        self.assertRaises(RestEasyException, lambda: taggable.serialize('nope'))

    def test_deserialize_success(self):
        data = {'model': 'rest_easy.MockModel', 'schema': 'default', 'value': 'zxc'}
        from rest_easy.registers import serializer_register
        validated = deserialize_data(data)
        self.assertEqual(validated, {'value': data['value']})

    def test_deserialize_failure(self):
        data = {'model': 'rest_easy.MockModel', 'value': 'zxc'}
        self.assertRaises(RestEasyException, lambda: deserialize_data(data))


class TestViews(unittest.TestCase):
    def test_missing_fields(self):
        class FailingViewSet(ModelViewSet):
            pass

        self.assertIsNone(FailingViewSet.queryset, None)

    def test_queryset(self):
        class TaggableViewSet(ModelViewSet):
            queryset = MockModel.objects.all()
            model = MockModel2

        class AccountViewSet(ModelViewSet):
            model = MockModel2

        self.assertEqual(TaggableViewSet.queryset.model, MockModel)
        self.assertEqual(AccountViewSet.queryset.model, MockModel2)

    def test_parent(self):
        class TaggableViewSet(ModelViewSet):
            model = MockModel
            scope = ScopeQuerySet(MockModel2)

        self.assertRaises(NotImplementedError, TaggableViewSet().get_queryset)


if __name__ == '__main__':
    unittest.main()
