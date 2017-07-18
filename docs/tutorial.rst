************
Introduction
************

Django-rest-easy is an extension to Django Rest Framework providing QOL improvements to serializers and views that introduce a more
coherent workflow for creating REST APIs:

* Versioning and referencing serializers by model and schema, along with autoimport, so your serializers will be available anywhere,
  as long as you know the model and schema.
* A :class:`rest_easy.fields.StaticField` for adding static data (independent of instance) to serializers.
* Creating views and viewsets using model and schema (it will automatically obtain serializer and queryset, although you can override
  both with usual DRF class-level parameters).
* Serializer override for a particular DRF verb, like create or update: no manual get_serialize_class override, no splitting ViewSets
  into multiple views.
* Scoping views\' querysets and viewsets by url kwargs or request object parameters when you want to limit messages to a particular
  thread or threads to currently logged in user.
* Adding your own base classes to `GenericView` and your own mixins to all resulting generic view classes, like `ListCreateAPIView`.
* Chaining views\' `perform_update` and `perform_create`: they by default pass \*\*kwargs to `serializer.save()` now.
* Helper mixin that enables serializing Django model instances with just an instance method call.
* Helper methods that find serializer class and deserialize a blob of data, since oftentimes you will not know what exact data you will
  receive in a particular endpoint, especially when dealing with complex integrations.

All of the above are possible in pure DRF, but usually introduce a lot of boilerplate or aren\'t very easy or straightforward to code,
thereferore at Telmediq we decided to open source the package that helps make our API code cleaner and more concise.

************
Installation
************

Django-rest-easy is available on PyPI. The simplest way to install it is by running `pip install django-rest-easy`. Afterwards you need
to add rest_easy to Django's `INSTALLED_APPS`::

    INSTALLED_APPS = (
        # ...
        'rest_framework',
        'rest_easy',
        # ...
    )

To make your serializers registered and working well with django-rest-easy\'s views, make sure they are autoimported. You can do that
either by importing them in `app.serializers` module or modifying `REST_EASY_AUTOIMPORT_SERIALIZERS_FROM` setting to include your
serializer location. For example, if you place your serializers in `app.api.serializers`, you should add the following to your settings
file::

    REST_EASY_AUTOIMPORT_SERIALIZERS_FROM = ['api.serializers']

Also, change your serializers to inherit from :class:`rest_easy.serializers.Serializer` or :class:`rest_easy.serializers.ModelSerializer`
instead of default DRF serializers. Same goes for views - you should be using this::

    from rest_easy.views import *

Instead of ::

    from rest_framework.generics import *

Additionally, the following settings can alter the behaviour of the package:

* REST_EASY_AUTOIMPORT_SERIALIZERS_FROM - specify modules or packages that rest-easy will try to import serializers
  from when AppConfig is ready. The import is app-based, so it will search for serializers in all installed apps.
  By default `['serializers']`
* REST_EASY_VIEW_BASES - your mixins that should go into all views near the end of the mro (before all DRF and
  django-rest-easy's bases, after all generic mixins from DRF).
* REST_EASY_GENERIC_VIEW_MIXINS - your mixins that should go into all generic views at the beginning of the mro
  (that means CreateAPIView, ListAPIView, RetrieveAPIView, DestroyAPIView,  UpdateAPIView,  ListCreateAPIView,
  RetrieveUpdateAPIView, RetrieveDestroyAPIView, RetrieveUpdateDestroyAPIView, ReadOnlyModelViewSet,
  ModelViewSet).
* REST_EASY_SERIALIZER_CONFLICT_POLICY - either 'allow' or 'raise'. What should happen when you redeclare a serializer
  with same model and schema - either the new one will be used or an error will be raised. By default 'allow' to not
  break applications with weird imports.

Because you usually won't be able to import the bases directly in settings, they should be given using class location strings (as is
often the case in Django)::

    REST_EASY_VIEW_BASES = ['myapp.mixins.GlobalBase']
    REST_EASY_GENERIC_VIEW_MIXINS = ['myapp.mixins.SuperMixin', 'myotherapp.mixins.WhatIsItMixin']

They will be prepended to base class lists preserving their order. Please make sure that you are not importing django-rest-easy views
before the mixins are ready to import (so before `AppConfig.ready` is called, for good measure).

***********
Basic usage
***********

A minimal example to showcase what you can do would be::

    from django.conf.urls import include, url
    from rest_framework.routers import DefaultRouter

    from rest_easy.serializers import ModelSerializer
    from rest_easy.views import ModelViewSet
    from rest_easy.scopes import UrlKwargScopeQuerySet
    from rest_easy.tests.models import Account, User

    class UserSerializer(ModelSerializer):
        class Meta:
            model = User
            schema = 'default'
            fields = '__all__'

    class UserViewSet(ModelViewSet):
        model = User
        schema = 'default'
        lookup_url_kwarg = 'pk'
        scope = UrlKwargScopeQuerySet(Account)

    router = DefaultRouter()
    router.register(r'accounts/(?P<account_pk>\d+)/users', UserViewSet)

    urlpatterns = [url(r'^', include(router.urls))]

**************
Detailed usage
**************

Serializers
===========

Django-rest-easy serializer bases (:class:`rest_easy.serializers.Serializer` and :class:`rest_easy.serializers.ModelSerializer`) are
registered on creation and provide some consistency constraints: each serializer needs to have model and schema set in its Meta. Schema
needs to be a string, while model should be a Django model subclass or explicit `None`. Both of those properties are required to be able
to register the serializer properly. Both are also appended to serializer's fields as :class:`rest_easy.fields.StaticField`. They will
be auto-included in `Meta.fields` when necessary (ie. fields is not `__all__`)::

    class UserSerializer(ModelSerializer):
        class Meta:
            model = User
            schema = 'default'
            fields = '__all__'

Serializers can be obtained easily from :class:`rest_easy.registers.SerializerRegister` (or, already instantiated,
`rest_easy.registers.serializer_register`) like so::

    from rest_easy.registers import serializer_register

    serializer = serializer_register.get('myapp.mymodel', 'default-schema')
    # or
    from myapp.models import MyModel
    serializer = serializer_register.get(MyModel, 'default-schema')
    # or
    serializer = serializer_register.get(None, 'modelless-schema')

This feature is leveraged heavily by django-rest-easy's views. Please remember that serializers need to be imported in order to be
registered - it's best achieved by using the auto-import functionality described in the installation section.

As for the :class:`rest_easy.fields.StaticField`, it can be used as such::

    class UserSerializer(ModelSerializer):
        class Meta:
            model = User
            schema = 'default'
            fields = '__all__'
        static_data = StaticField(value='static_value')

Views
=====

Views and viewsets provide a few additional features, allowing you to not specify `queryset` and `serializer_class` properties by
default. If they are specified, though, they take priority over any logic provided by django-rest-easy.

* Providing `serializer_class` will disable per-verb custom serializers. It will make the view act basically as regular DRF view.
* `queryset` property doesn't disable any functionality. By default it is set to `model.objects.all()`, where model is provided as a
  class property, but it can be overridden at will without messing with django-rest-easy's functionality.

Overall using serializer_class on django-rest-easy views is not recommended.

A view example showing available features::

    class UserViewSet(ModelViewSet):
        model = User
        schema = 'default'
        serializer_schema_for_verb = {'update': 'schema-mutate', 'create': 'schema-mutate'}
        lookup_url_kwarg = 'pk'
        scope = UrlKwargScopeQuerySet(Account)

        def perform_update(self, serializer, **kwargs):
            kwargs['account'] = self.get_account()
            return super(UserViewSet, self).perform_update(serializer, **kwargs)

        def perform_create(self, serializer, **kwargs):
            kwargs['account'] = self.get_account()
            return super(UserViewSet, self).perform_create(serializer, **kwargs)

We're setting `User` as model, so the inferred queryest will be `User.objects.all()`. When a request comes in, a proper serializer will
be selected:

* If the DRF dispatcher will call update or create methods, we will use serializer obtained by calling
  `serializer_register.get(User, 'schema-mutate')`.
* Otherwise the default schema will be used, so `serializer_register.get(User, 'default')`.

Additionally we're scoping the Users by account. In short, that means (by default - more on that in the section below) that our base
queryset is modified with::

    queryset = queryset.filter(account=Account.objects.get(pk=self.kwargs.get('account_pk')))

Also, helper methods are provided for each scope that doesn't disable it::

    def get_account(self):
        return Account.objects.get(pk=self.kwargs.get('account_pk'))

Technically, they are implemented with `__getattr__`, but each scope which doesn\'t have get_object_handle set to None
will provide a get_X method (like `get_account` above) to obtain the object used for filtering. The object is kept cached
on the view instance, so it can be reused during request handling without additional database queries. If the get_X method
would be shadowed by something else, all scoped object are available via `view.get_scoped_object`::

    def perform_create(self, serializer, **kwargs):
        kwargs['account'] = self.get_scoped_object('account')
        return super(UserViewSet, self).perform_create(serializer, **kwargs)

This follows standard Django convention of naming foreign keys by `RelatedModel._meta.model_name` (same as scoped object access
on view), using pk as primary key and modelname_pk as url kwarg. All of those parameters are configurable (see Scopes section below).

For more complex cases, you can provide a list of scopes instead of a single scope. All of them will be applied to the queryset.

Now let's say all your models need to remember who modified them recently. You don't really want to pass the logged in user to
serializer in each view, and using threadlocals or globals isn't a good idea for this type of task. The solution to this problem
would be a common view mixin. Let's say we place this in `myapp.mixins.py`::

    class InjectUserMixin(object):
        def perform_update(self, serializer, **kwargs):
            kwargs['user'] = self.request.user
            return super(UserViewSet, self).perform_update(serializer, **kwargs)

        def perform_create(self, serializer, **kwargs):
            kwargs['user'] = self.request.user
            return super(UserViewSet, self).perform_create(serializer, **kwargs)

And set `REST_EASY_GENERIC_VIEW_MIXINS` in your Django settings to::

    REST_EASY_GENERIC_VIEW_MIXINS = ['myapp.mixins.InjectUserMixin']

Now all serializers will receive user as a parameter when calling `save()` from a update or create view.

Scopes
======

Scopes are used to apply additional filters to views' querysets based on data obtainable form kwargs
(:class:`rest_easy.scopes.UrlKwargScopeQuerySet`) and request (:class:`rest_easy.scopes.RequestAttrScopeQuerySet`). They should be used
remove the boilerplate and bloat coming from filtering inside get_queryset or in dedicated mixins by providing a configurable wrapper
for the filtering logic.

There is also a base :class:`rest_easy.scopes.ScopeQuerySet` that you can inherit from to provide your own logic. When called, the
ScopeQuerySet instance receives whole view object as a parameter, so it has access to everything that happens during the request as well
as in application as a whole.

Scopes can be chained (that is you can filter scope's queryset using another scope, just as it was a view; this supports lists of scopes
as well). An example would be::

    class MessageViewSet(ModelViewSet):
        model = Message
        schema = 'default'
        lookup_url_kwarg = 'pk'
        scope = UrlKwargScopeQuerySet(Thread, parent=UrlKwargScopeQuerySet(Account))

ScopeQuerySet
-------------

When instantiating it, it accepts the following parameters (`{value}` is the filtering value obtained by concrete Scope implementation):

* qs_or_obj: a queryset or model (in that case, the queryset would be `model.objects.all()`) that the scope works on. This can also
  be `None` in special cases (for example, when using :class:`rest_easy.scopes.RequestAttrScopeQuerySet` with `is_object=True`).
  For example, assuming you have a model Message that has foreign key to Thread, when scoping a `MessageViewSet` you would use
  `scope = ScopeQuerySet(Thread)`.
* parent_field: the field qs_or_obj should be filtered by. By default it is pk. Following the example, the scope above would find the
  Thread object by `Thread.objects.all().filter(pk={value})`.
* raise_404: If the instance we\'re scoping by isn\'t found (in the example, Thread with pk={value}), whether a 404 exception should be
  raised or should we continue as usual. By default False
* allow_none: If the instance we\'re scoping by isn\'t found and 404 is not raised, whether to allow filtering child queryset with None
  (`allow_none=True`) or not - in this case we will filter with model.objects.none() and guarantee no results (`allow_none=False`).
  False by default.
* get_object_handle: the name under which the object used for filtering (either None or result of applying {value} filter to queryset)
  will be available on the view. By default this is inferred to model_name. Can be set to None to disable access. It can be accessed
  from view as view.get_{get_object_handle}, so when using the above example, view.get_thread(). If the get_x method would be
  shadowed by something else, there is an option to call view.get_scoped_object(get_object_handle), so for example
  view.get_scoped_object(thread).
* parent: parent scope. If present, qs_or_obj will be filtered by the scope or scopes passed as this parameter, just as if this was a
  view.

UrlKwargScopeQuerySet
---------------------

It obtains filtering value from `view.kwargs`. It takes one additional keyword argument:

* url_kwarg: what is the name of kwarg (as given in url config) which has the value to filter by. By default it is configured to be
  model_name_pk (model name is obtained from qs_or_obj).

Example::

    scope = UrlKwargScopeQuerySet(Message.objects.active(), parent_field='uuid', url_kwarg='message_uuid', raise_404=True)
    queryset = scope.child_queryset(queryset, view)
    # is equal to roughly:
    queryset = queryset.filter(message=Message.objects.active().get(uuid=view.kwargs.get('message_uuid'))

RequestAttrScopeQuerySet
------------------------

It obtains the filtering value from `view.request`. It takes two additional keyword arguments:

* request_attr: the attribute in `view.request` that contains the filtering value or the object itself.
* is_object: whether the request attribute contains object (True) or filtering value (False). By default True.

Example with `is_object=True`::

    scope = RequestAttrScopeQuerySet(User, request_attr='user')
    queryset = scope.child_queryset(queryset, view)
    # is roughly equal to:
    queryset = queryset.filter(user=view.request.user)

Example with `is_object=False`::

    scope = RequestAttrScopeQuerySet(User, request_attr='user', is_object=False)
    queryset = scope.child_queryset(queryset, view)
    # is roughly equal to:
    queryset = queryset.filter(user=User.objects.get(pk=view.request.user))

Helpers
=======

There are following helpers available in :mod:`rest_easy.models`:

* :class:`rest_easy.models.SerializableMixin` - it's supposed to be used on models. It provides
  :func:`rest_easy.models.SerializableMixin.get_serializer` method for obtaining model serializer given a schema and
  :func:`rest_easy.models.SerializableMixin.serialize` to serialize data (given schema or None, in which case the default schema is
  used. It can be set on a model, initially it's just `'default'`).
* :func:`rest_easy.models.get_serializer` - looking at a blob of data, it obtains the serializer from register based on `data['model']`
  and `data['schema']`.
* :func:`rest_easy.models.deserialize_data` - deserializes a blob of data if appropriate serializer is found.
