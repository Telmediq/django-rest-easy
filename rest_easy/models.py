# coding: utf-8
"""
This module provides useful model mixins and global functions.

Its contents can be used to serialize a model or find proper serializer/deserialize data via a registered serializer.
"""

from __future__ import unicode_literals

from rest_easy.exceptions import RestEasyException
from rest_easy.registers import serializer_register

__all__ = ['SerializableMixin', 'get_serializer', 'deserialize_data']


class SerializableMixin(object):
    """
    This mixin provides serializing functionality to Django models.

    The serializing is achieved thanks to serializers registered in
    :class:`rest_easy.registers.SerializerRegister`. A proper serializer based on model and provided
    schema is obtained from the register and the serialization process is delegated to it.

    Usage:

    ```python
    from users.models import User
    serializer = User.get_serializer(User.default_schema)
    ```
    Or:

    ```python
    data = User.objects.all()[0].serialize()
    ```
    """
    default_schema = 'default'

    @classmethod
    def get_serializer(cls, schema):
        """
        Get correct serializer for this model and given schema,

        Utilizes :class:`rest_easy.registers.SerializerRegister` to obtain correct serializer class.
        :param schema: schema to be used for serialization.
        :return: serializer class.
        """
        name = serializer_register.get_name(cls, schema)
        return serializer_register.lookup(name)

    def serialize(self, schema=None):
        """
        Serialize the model using given or default schema.
        :param schema: schema to be used for serialization or self.default_schema
        :return: serialized data (a dict).
        """
        serializer = self.get_serializer(schema or self.default_schema)
        if not serializer:
            raise RestEasyException('No serializer found for model {} schema {}'.format(self.__class__, schema))
        return serializer(self).data


def get_serializer(data):
    """
    Get correct serializer for dict-like data.

    This introspects model and schema fields of the data and passes them to
    :class:`rest_easy.registers.SerializerRegister`.
    :param data: dict-like object.
    :return: serializer class.
    """
    if 'model' not in data or 'schema' not in data:
        raise RestEasyException('Both model and schema must be provided in data~.')
    serializer = serializer_register.lookup(serializer_register.get_name(data['model'], data['schema']))
    if not serializer:
        raise RestEasyException('No serializer found for model {} schema {}'.format(data['model'], data['schema']))
    return serializer


def deserialize_data(data):
    """
    Deserialize dict-like data.

    This function will obtain correct serializer from :class:`rest_easy.registers.SerializerRegister`
    using :func:`rest_easy.models.get_serializer`.
    :param data: dict-like object or json string.
    :return: Deserialized, validated data.
    """
    serializer = get_serializer(data)(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data
