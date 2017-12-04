# coding: utf-8
"""
This module contains base serializers to be used with django-rest-easy.

Crucial point of creating a good API is format consistency. If you've been lacking that so far, can't afford it anymore
or want to make your life easier, you can enforce a common message format and a common serialization format.
Enter the following SerializerCreator - it will make sure that everything serializers output will contain schema
and model fields. This affects both regular and model serializers.

Additional benefit of using such metaclass is serializer registration - we can easily obtain serializers based on
model (or None for non-model serializers) and schema from anywhere in the application. That's useful in several cases:

* model serialization
* remote data deserialization (no changes to (de)serialization logic required when we add a new schema)
* simpler views and viewsets

This doesn't disable any DRF's serializers functionality.
"""
from __future__ import unicode_literals

import six
from django.db import models
from rest_framework.serializers import (Serializer as OSerializer,
                                        ModelSerializer as OModelSerializer,
                                        SerializerMetaclass,
                                        Field)

from rest_easy.fields import StaticField
from rest_easy.registers import serializer_register
from rest_easy.patterns import RegisteredCreator

__all__ = ['ModelSerializer', 'Serializer', 'RegisterableSerializerMixin', 'SerializerCreator']


class SerializerCreator(RegisteredCreator, SerializerMetaclass):
    """
    This metaclass creates serializer classes to be used with django-rest-easy.

    We need to employ multiple inheritance here (if the behaviour ever needs to be overridden, you can just use both
    base classes to implement your own functionality) to preserve DRF's behaviour regarding
    serializer fields as well as registration and required fields checking from our own metaclass.

    Remember that all __new__ methods from base classes get called.
    """
    inherit_fields = False
    register = serializer_register
    required_fields = {
        'Meta': {
            'model': lambda value: value is None or issubclass(value, models.Model),
            'schema': lambda value: isinstance(value, six.string_types)
        }
    }

    @staticmethod
    def get_fields_from_base(base):
        """
        Alteration of original fields inheritance.

        It skips all serializer fields, since SerializerMetaclass deals with that already.
        :param base: a base class.
        :return: generator of (name, value) tuples of fields from base.
        """
        for item in dir(base):
            # Avoid copying serializer fields to class, since DRF's metaclass deals with that already.
            if not item.startswith('_') and not isinstance(item, Field):
                value = getattr(base, item)
                if not callable(value):
                    yield item, getattr(base, item)

    @staticmethod
    def get_name(name, bases, attrs):
        """
        Alteration of original get_name.

        This, instead of returing class's name, obtains correct serializer registration name from
        :class:`rest_easy.registers.SerializerRegister` and uses it as slug for registration purposes.
        :param name: class name.
        :param bases: class bases.
        :param attrs: class attributes.
        :return: registered serializer name.
        """
        model = attrs['Meta'].model
        return serializer_register.get_name(model, attrs['Meta'].schema)

    @classmethod
    def pre_register(mcs, name, bases, attrs):
        """
        Pre-register hook adding required fields

        This is the place to add required fields if they haven't been declared explicitly.
        We're adding model and schema fields here.
        :param name: class name.
        :param bases: class bases.
        :param attrs: class attributes.
        :return: tuple of altered name, bases, attrs.
        """
        if 'model' not in attrs:
            model = attrs['Meta'].model
            if model:
                model_name = '{}.{}'.format(model._meta.app_label, model._meta.object_name)  # pylint: disable=protected-access
            else:
                model_name = None
            attrs['model'] = StaticField(model_name)
        if 'schema' not in attrs:
            attrs['schema'] = StaticField(attrs['Meta'].schema)
        if hasattr(attrs['Meta'], 'fields'):
            if not isinstance(attrs['Meta'].fields, six.string_types):
                attrs['Meta'].fields = list(attrs['Meta'].fields)
                if 'model' not in attrs['Meta'].fields:
                    attrs['Meta'].fields.append('model')
                if 'schema' not in attrs['Meta'].fields:
                    attrs['Meta'].fields.append('schema')
        return name, bases, attrs


class RegisterableSerializerMixin(six.with_metaclass(SerializerCreator, object)):  # pylint: disable=too-few-public-methods
    """
    A mixin to be used if you want to inherit functionality from non-standard DRF serializer.
    """
    __abstract__ = True


class Serializer(six.with_metaclass(SerializerCreator, OSerializer)):  # pylint: disable=too-few-public-methods,abstract-method
    """
    Registered version of DRF's Serializer.
    """
    __abstract__ = True


class ModelSerializer(six.with_metaclass(SerializerCreator, OModelSerializer)):  # pylint: disable=too-few-public-methods,abstract-method
    """
    Registered version of DRF's ModelSerializer.
    """
    __abstract__ = True
