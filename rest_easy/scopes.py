# coding: utf-8
"""
This module provides scopes usable with django-rest-easy's generic views.

See :mod:`rest_easy.views` for detailed explanation.
"""
from __future__ import unicode_literals

from django.db.models import QuerySet, Model
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_easy.exceptions import RestEasyException

__all__ = ['ScopeQuerySet', 'UrlKwargScopeQuerySet', 'RequestAttrScopeQuerySet']


class ScopeQuerySet(object):
    """
    This class provides a scope-by-parent-element functionality to views and their querysets.

    It works by selecting a proper parent model instance and filtering view's queryset with it automatically.
    """

    def __init__(self, qs_or_obj, parent_field='pk', related_field=None, raise_404=False, allow_none=False,
                 get_object_handle='', parent=None):
        """
        Sets instance properties, infers sane defaults and ensures qs_or_obj is correct.

        :param qs_or_obj: This can be a queryset or a Django model or explicit None (for particular subclasses)
        :param parent_field: the field to filter by in the parent queryset (qs_or_obj), by default 'id'.
        :param related_field: the field to filter by in the view queryset, by default model_name.
        :param raise_404: whether 404 should be raised if parent object cannot be found.
        :param allow_none: if filtering view queryset by object=None should be allowed. If it's false, resulting
         queryset is guaranteed to be empty if parent object can't be found and 404 is not raised.
        :param get_object_handle: the name under which the object should be available in view. ie.
         view.get_scoped_object(get_object_handle) or view.get_{get_object_handle}. If None, the object will
         not be available from view level. By default will be infered to qs_or_obj's model_name.
        :param parent: if this object's queryset should be filtered by another parameter, parent attribute should be
         an instance of ScopeQuerySet. This allows for ScopeQuerySetChaining (ie. for messages we might have
         UrlKwargScopeQuerySet(User, parent=UrlKwargScopeQuerySet(Account))  for scoping by user and limiting users
         to an account.
        """
        if isinstance(qs_or_obj, QuerySet):
            self.queryset = qs_or_obj
        elif isinstance(qs_or_obj, type) and issubclass(qs_or_obj, Model):
            self.queryset = qs_or_obj.objects.all()
        elif qs_or_obj is None:
            self.queryset = None
        else:
            raise RestEasyException('Queryset parameter must be an instance of QuerySet or a Model subclass.')

        if related_field is None:
            try:
                related_field = '{}'.format(self.queryset.model._meta.model_name)  # pylint: disable=protected-access
            except AttributeError:
                raise RestEasyException('Either related_field or qs_or_obj must be given.')
        self.parent_field = parent_field
        self.related_field = related_field
        self.raise_404 = raise_404
        self.parent = ([parent] if isinstance(parent, ScopeQuerySet) else parent) or []
        self.allow_none = allow_none
        self.get_object_handle = get_object_handle
        if self.get_object_handle == '':
            try:
                self.get_object_handle = self.queryset.model._meta.model_name  # pylint: disable=protected-access
            except AttributeError:
                raise RestEasyException('Either qs_or_obj or explicit get_object_handle (can be None) must be given.')

    def contribute_to_class(self, view):
        """
        Put self.get_object_handle into view's available handles dict to allow easy access to the scope's get_object()
        method in case the object needs to be reused (ie. in child object creation).
        :param view: View the scope is added to.
        """
        if self.get_object_handle:
            if self.get_object_handle in view.rest_easy_available_object_handles:
                raise RestEasyException(
                    'ImproperlyConfigured: multiple scopes with {} get_object handle!'.format(self.get_object_handle)
                )
            view.rest_easy_available_object_handles[self.get_object_handle] = self
        for scope in self.parent:
            scope.contribute_to_class(view)

    def get_value(self, view):
        """
        Get value used to filter qs_or_objs's field specified for filtering (parent_field in init).
        :param view: DRF view instance - as it provides access to both request and kwargs.
        :return: value to filter by.
        """
        raise NotImplementedError('You need to use ScopeQueryset subclass with get_value implemented.')

    def get_queryset(self, view):
        """
        Obtains parent queryset (init's qs_or_obj) along with any chaining (init's parent) required.
        :param view: DRF view instance.
        :return: queryset instance.
        """
        queryset = self.queryset
        for parent in self.parent:
            queryset = parent.child_queryset(queryset, view)
        return queryset

    def get_object(self, view):
        """
        Caching wrapper around _get_object.
        :param view: DRF view instance.
        :return: object (instance of init's qs_or_obj model except shadowed by subclass).
        """
        if self.get_object_handle:
            obj = view.rest_easy_object_cache.get(self.get_object_handle, None)
            if not obj:
                obj = self._get_object(view)
                view.rest_easy_object_cache[self.get_object_handle] = obj
        else:
            obj = self._get_object(view)
        return obj

    def _get_object(self, view):
        """
        Obtains parent object by which view queryset should be filtered.
        :param view: DRF view instance.
        :return: object (instance of init's qs_or_obj model except shadowed by subclass).
        """
        queryset = self.get_queryset(view)
        queryset = queryset.filter(**{self.parent_field: self.get_value(view)})
        try:
            obj = get_object_or_404(queryset)
        except Http404:
            if self.raise_404:
                raise
            obj = None
        return obj

    def child_queryset(self, queryset, view):
        """
        Performs filtering of the view queryset.
        :param queryset: view queryset instance.
        :param view: view object.
        :return: filtered queryset.
        """
        obj = self.get_object(view)
        if obj is None and not self.allow_none:
            return queryset.none()
        return queryset.filter(**{self.related_field: obj})


class UrlKwargScopeQuerySet(ScopeQuerySet):
    """
    ScopeQuerySet that obtains parent object from url kwargs.
    """

    def __init__(self, *args, **kwargs):
        """
        Adds url_kwarg to :class:`rest_easy.views.ScopeQuerySet` init parameters.

        :param args: same as :class:`rest_easy.views.ScopeQuerySet`.
        :param url_kwarg: name of url field to be obtained from view's kwargs. By default it will be inferred as
         model_name_pk.
        :param kwargs: same as :class:`rest_easy.views.ScopeQuerySet`.
        """
        self.url_kwarg = kwargs.pop('url_kwarg', None)
        super(UrlKwargScopeQuerySet, self).__init__(*args, **kwargs)
        if not self.url_kwarg:
            try:
                self.url_kwarg = '{}_pk'.format(self.queryset.model._meta.model_name)  # pylint: disable=protected-access
            except AttributeError:
                raise RestEasyException('Either related_field or qs_or_obj must be given.')

    def get_value(self, view):
        """
        Obtains value from url kwargs.
        :param view: DRF view instance.
        :return: Value determining parent object.
        """
        return view.kwargs.get(self.url_kwarg)


class RequestAttrScopeQuerySet(ScopeQuerySet):
    """
    ScopeQuerySet that obtains parent object from view's request property.

    It can work two-fold:

    * the request's property contains full object: in this case no filtering of parent's queryset is required. When
      using such approach, is_object must be set to True, and qs_or_obj can be None. Chaining will be disabled since it
      is inherent to filtering process.
    * the request's property contains object's id, uuid, or other unique property. In that case is_object needs to be
      explicitly set to False, and qs_or_obj needs to be a Django model or queryset. Chaining will be performed as
      usually.

    """

    def __init__(self, *args, **kwargs):
        """
        Adds is_object and request_attr  to :class:`rest_easy.views.ScopeQuerySet` init parameters.

        :param args: same as :class:`rest_easy.views.ScopeQuerySet`.
        :param request_attr: name of property to be obtained from view.request.
        :param is_object: if request's property will be an object or a value to filter by. True by default.
        :param kwargs: same as :class:`rest_easy.views.ScopeQuerySet`.
        """
        self.request_attr = kwargs.pop('request_attr', None)
        if self.request_attr is None:
            raise RestEasyException('request_attr must be set explicitly on an {} init.'.format(
                self.__class__.__name__))
        self.is_object = kwargs.pop('is_object', True)
        super(RequestAttrScopeQuerySet, self).__init__(*args, **kwargs)

    def get_value(self, view):
        """
        Obtains value from url kwargs.
        :param view: DRF view instance.
        :return: Value determining parent object.
        """
        return getattr(view.request, self.request_attr, None)

    def _get_object(self, view):
        """
        Extends standard _get_object's behaviour with handling values that are already objects.
        :param view: DRF view instance.
        :return: object to filter view's queryset by.
        """
        if self.is_object:
            return self.get_value(view)
        return super(RequestAttrScopeQuerySet, self)._get_object(view)
