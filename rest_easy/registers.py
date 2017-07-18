# coding: utf-8
"""
This module contains the serializer register.

The serializer register is where all serializers created using
:class:`rest_easy.serializers.SerializerCreator` are registered and where they can be obtained from based
on model and schema. Remember that no other serializers will be kept here - and they will not be obtainable in such
a way.
"""
from __future__ import unicode_literals

import six

from rest_easy.exceptions import RestEasyException
from rest_easy.patterns import BaseRegister

__all__ = ['SerializerRegister', 'serializer_register']


class SerializerRegister(BaseRegister):
    """
    Obtains serializer registration name based on model and schema.
    """
    @staticmethod
    def get_name(model, schema):
        """
        Constructs serializer registration name using model's app label, model name and schema.
        :param model: a Django model, a ct-like app-model string (app_label.modelname) or explicit None.
        :param schema: schema to be used.
        :return: constructed serializer registration name.
        """
        if model is None:
            return schema
        if isinstance(model, six.string_types):
            return '{}.{}'.format(model, schema)
        try:
            return '{}.{}.{}'.format(model._meta.app_label, model._meta.model_name, schema)  # pylint: disable=protected-access
        except AttributeError:
            raise RestEasyException('Model must be either None, a ct-like model string or Django model class.')

    def get(self, model, schema):
        """
        Shortcut to get serializer having model and schema.
        """
        return self.lookup(self.get_name(model, schema))

serializer_register = SerializerRegister()
