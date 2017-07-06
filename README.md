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
from rest_easy.serializers import ModelSerializer
from rest_easy.views import ModelViewSet, UrlKwargScopeQuerySet

from messages import Message
from users import User

class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

    schema = StaticField('default')

class MessageViewSet(ModelViewSet):
    model = Message
    schema = 'default'
    scope = UrlKwargScopeQuerySet(User)

router.register(r'users/(?P<user_pk>\d+)/messages', MessageViewSet)
```

Installation
------------
`pip install django-rest-easy`

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

We use Travis CI. The targets are 10.00 for lint and 100% for coverage, as well as building sphinx docs.

You can also check the build manually, just make sure to `pip install -r requirements.txt` before:

```
pylint rest_easy --rcfile=.pylintrc
coverage run --source=rest_easy -m rest_easy.tests && coverage report -m
sphinx-apidoc -o docs/auto rest_easy -f
cd docs && make html
```

Additionally you can check cyclomatic complexity and maintenance index with radon:

```
radon cc rest_easy
radon mi rest_easy
```

The target is A for maintenance index, C for cyclomatic complexity - but don't worry if it isn't met, I can
refactor it after merging.
