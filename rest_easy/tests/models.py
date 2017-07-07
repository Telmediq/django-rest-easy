# coding: utf-8
# pylint: skip-file
from __future__ import unicode_literals

from django.db import models

from rest_easy.models import SerializableMixin


class MockModel(SerializableMixin, models.Model):
    class Meta:
        app_label = 'rest_easy'

    value = models.CharField(max_length=50)


class MockModel2(SerializableMixin, models.Model):
    class Meta:
        app_label = 'rest_easy'

    value = models.CharField(max_length=50)


class Account(SerializableMixin, models.Model):
    class Meta:
        app_label = 'rest_easy'


class User(SerializableMixin, models.Model):
    class Meta:
        app_label = 'rest_easy'
    account = models.ForeignKey(Account)
