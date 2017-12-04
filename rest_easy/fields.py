# coding: utf-8
"""
This module contains fields necessary for the django-rest-easy module.
"""
from __future__ import unicode_literals

from rest_framework.fields import Field

__all__ = ['StaticField']


class StaticField(Field):  # pylint: disable=abstract-method
    """
    A field that always provides the same value as output.

    The output value is set on initialization, ie::

        from rest_easy.serializers import Serializer

        class MySerializer(Serializer):
            static = StaticField('This will always be the value.')

    """

    def __init__(self, value, **kwargs):
        """
        Initialize the instance with value and DRF settings.
        """
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(StaticField, self).__init__(**kwargs)
        self.value = value

    def to_representation(self, value):
        """
        Return the static value.
        """
        return self.value
