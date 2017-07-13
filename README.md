django-rest-easy
================

[![Build Status](https://travis-ci.org/TelmedIQ/django-rest-easy.svg)](https://travis-ci.org/TelmedIQ/django-rest-easy)

django-rest-easy is an extension to DRF providing QOL improvements to serializers and views.
It enables:

* versioning serializers by model and schema,
* creating views and viewsets using model and schema,
* serializer override for a particular DRF verb, like create or update,
* scoping views\' querysets and viewsets by url kwargs or request object parameters.

### Basic usage

```python
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
router.register(r'users/(?P<user_pk>\d+)/messages', UserViewSet)

urlpatterns = [url(r'^', include(router.urls))]
```

Installation
------------
`pip install django-rest-easy` and add rest_easy to installed apps in Django settings.

The settings used are:

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

Documentation
-------------

Feel free to browse the code and especially the tests to see what's going on behind the scenes.
The current version of docs is available on http://django-rest-easy.readthedocs.org/en/latest/.

Questions and contact
---------------------

If you have any questions, feedback, want to say hi or talk about Python, just hit me up on
https://twitter.com/bujniewicz

Contributions
-------------

Please read CONTRIBUTORS file before submitting a pull request.

We use Travis CI. The targets are 10.00 for lint and non-decreasing coverage (currently at 100%), as well as
building sphinx docs.

You can also check the build manually, just make sure to `pip install -r requirements.txt` before:

```
pylint rest_easy --rcfile=.pylintrc
coverage run --source=rest_easy -m rest_easy.runtests && coverage report -m
sphinx-apidoc -o docs/auto rest_easy -f
cd docs && make html
```

Additionally you can check cyclomatic complexity and maintenance index with radon:

```
radon cc rest_easy
radon mi rest_easy
```

The target is A for maintenance index, B for cyclomatic complexity - but don't worry if it isn't met, I can
refactor it after merging.
