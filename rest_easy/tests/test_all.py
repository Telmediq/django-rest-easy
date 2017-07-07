# coding: utf-8
# pylint: skip-file
"""
Tests for django-rest-easy. So far not ported from proprietary code.
"""
from __future__ import unicode_literals

from django.http import Http404
from django.test import TestCase

from rest_easy.exceptions import RestEasyException
from rest_easy.models import deserialize_data
from rest_easy.serializers import ModelSerializer
from rest_easy.views import ModelViewSet
from rest_easy.scopes import ScopeQuerySet, UrlKwargScopeQuerySet
from rest_easy.tests.models import *


class BaseTestCase(TestCase):
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
        validated = deserialize_data(data)
        self.assertEqual(validated, {'value': data['value']})

    def test_deserialize_failure(self):
        data = {'model': 'rest_easy.MockModel', 'value': 'zxc'}
        self.assertRaises(RestEasyException, lambda: deserialize_data(data))


class TestViews(BaseTestCase):
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


class Container(object):
    pass


class TestScopeQuerySet(BaseTestCase):
    def setUp(self):
        self.account = Account.objects.create()
        self.other_account = Account.objects.create()
        self.user = User.objects.create(account=self.account)
        self.other_user = User.objects.create(account=self.other_account)

    def test_chaining(self):
        self.assertRaises(NotImplementedError, lambda: UrlKwargScopeQuerySet(Account,
                                                                             parent=ScopeQuerySet(Account)
                                                                             ).child_queryset(None, None))

    def test_url_kwarg(self):
        view = Container()
        view.kwargs = {'account_pk': self.other_account.pk}

        qs = UrlKwargScopeQuerySet(Account).child_queryset(User.objects.all(), view)
        self.assertIn(self.other_user, list(qs))
        self.assertEqual(1, len(list(qs)))

    def test_none(self):
        view = Container()
        view.kwargs = {'account_pk': self.other_account.pk + 100}

        qs = UrlKwargScopeQuerySet(Account).child_queryset(User.objects.all(), view)
        self.assertEqual(0, len(list(qs)))

    def test_raises(self):
        view = Container()
        view.kwargs = {'account_pk': self.other_account.pk + 100}

        self.assertRaises(Http404,
                          lambda: UrlKwargScopeQuerySet(Account,
                                                        raise_404=True).child_queryset(User.objects.all(), view))
