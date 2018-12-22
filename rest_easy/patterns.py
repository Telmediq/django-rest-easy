"""
This class defines generic bases for a few design / architectural patterns
required by django-rest-easy, namely singleton and register.
"""

from functools import wraps
from six import with_metaclass

from rest_easy.exceptions import RestEasyException

__all__ = ['SingletonCreator', 'SingletonBase', 'Singleton', 'BaseRegister', 'RegisteredCreator']

class SingletonCreator(type):
    """
    This metaclass wraps __init__ method of created class with singleton_decorator.
    This ensures that it's impossible to mess up the instance for example by
    calling __init__ with getattr.
    """

    @staticmethod
    def singleton_decorator(func):
        """
        We embed given function into checking if the first (zeroth) parameter of its call
        shall be initialised.
        :param func: instantiating function (usually __init__).
        :returns: embedded function function.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            This inner function checks init property of given instance and depending on its
            value calls the function or not.
            """
            if args[0].sl_init:
                return func(*args, **kwargs)
            return None

        return wrapper

    def __new__(mcs, name, bases, attrs):
        """
        Wraps are awesome. Sometimes.
        """
        if not (len(bases) == 1 and object in bases):
            if '__init__' in attrs:
                attrs['__init__'] = mcs.singleton_decorator(attrs['__init__'])
        return super(SingletonCreator, mcs).__new__(mcs, name, bases, attrs)


class SingletonBase(object):  # pylint: disable=too-few-public-methods
    """
    This class implements the singleton pattern using a metaclass and
    overriding default __new__ magic method's behaviour. It works together with
    SingletonCreator metaclass to create a Singleton base class.
    sl_init property is reserved, you can't use it in inheriting classes.
    """

    _instance = None

    def __new__(cls, *_):
        """
        This magic method override makes sure that only one instance will be created.
        """
        if not isinstance(cls._instance, cls):
            cls._instance = super(SingletonBase, cls).__new__(cls)
            cls._instance.sl_init = True
        else:
            cls._instance.sl_init = False
        return cls._instance


class Singleton(with_metaclass(SingletonCreator, SingletonBase)):  # pylint: disable=too-few-public-methods
    """
    This is a Singleton you can inherit from.
    It reserves sl_init instance attribute to work properly.
    """


class BaseRegister(Singleton):
    """
    This class is a base register-type class. You should inherit from it to create particular registers.

    conflict_policy is a setting deciding what to do in case of name collision (registering another
    entity with the same name). It should be one of:

    * allow - replace old entry with new entry, return True,
    * deny - leave old entry, return False,
    * raise - raise RestEasyException.

    Default policy is raise.

    As this is a singleton, instantiating a particular children class in any place will yield the exact same data
    as the register instance used in RegisteredCreator().
    """
    conflict_policy = 'allow'

    @classmethod
    def get_conflict_policy(cls):
        """
        Obtain conflict policy from django settings or use default.

        Allowed settings are 'raise' and 'allow'. Default is 'raise'.
        """
        from django.conf import settings
        return getattr(settings, 'REST_EASY_SERIALIZER_CONFLICT_POLICY', cls.conflict_policy)

    def __init__(self):
        """
        We create an empty model dict.
        """
        self._entries = {}
        self.connect = lambda: None

    def register(self, name, ref):
        """
        Register an entry, shall we?
        :param name: entry name.
        :param ref: entry value (probably class).
        :returns: True if model was added just now, False if it was already in the register.
        """
        if not self.lookup(name) or self.get_conflict_policy() == 'allow':
            self._entries[name] = ref
            return True
        raise RestEasyException('Entry named {} is already registered.'.format(name))

    def lookup(self, name):
        """
        I like to know if an entry is in the register, don't you?
        :param name: name to check.
        :returns: True if entry with given name is in the register, False otherwise.
        """
        return self._entries.get(name, None)

    def entries(self):
        """
        Return an iterator over all registered entries.
        """
        return self._entries.items()


class RegisteredCreator(type):
    """
    This metaclass integrates classes with a BaseRegister subclass.

    It skips processing base/abstract classes, which have __abstract__ property
    evaluating to True.
    """
    register = None
    required_fields = set()
    inherit_fields = False

    @staticmethod
    def get_name(name, bases, attrs):  # pylint: disable=unused-argument
        """
        Get name to be used for class registration.
        """
        return name

    @staticmethod
    def get_fields_from_base(base):
        """
        Obtains all fields from the base class.
        :param base: base class.
        :return: generator of (name, value) tuples.
        """
        for item in dir(base):
            if not item.startswith('_'):
                value = getattr(base, item)
                if not callable(value):
                    yield item, getattr(base, item)

    @classmethod
    def process_required_field(mcs, missing, fields, name, value):
        """
        Processes a single required field to check if it applies to constraints.
        """
        try:
            if not hasattr(fields, name) and name not in fields:
                missing.append(name)
                return
        except TypeError:
            missing.append(name)
            return
        if value:
            if hasattr(fields, name):
                inner = getattr(fields, name)
            else:
                inner = fields[name]
            if callable(value):
                if not value(inner):
                    missing += [name]
            else:
                missing += [name + '.' + item for item in mcs.get_missing_fields(value, inner)]

    @classmethod
    def get_missing_fields(mcs, required_fields, fields):
        """
        Lists required fields that are missing.

        Supports two formats of input of required fields: either a simple set {'a', 'b'} or a dict with several
        options::

            {
                'nested': {
                    'presence_check_only': None,
                    'functional_check': lambda value: isinstance(value, Model)
                },
                'flat_presence_check': None,
                'flat_functional_check': lambda value: isinstance(value, Model)
            }

        Functional checks need to return true for field not to be marked as missing.
        Dict-format also supports both dict and attribute based accesses for fields (fields['a'] and fields.a).

        :param required_fields: set or dict of required fields.
        :param fields: dict or object of actual fields.
        :return: List of missing fields.
        """
        if isinstance(required_fields, set):
            return [field for field in required_fields if field not in fields or not field]

        missing = []
        for name, value in required_fields.items():
            mcs.process_required_field(missing, fields, name, value)
        return missing

    @classmethod
    def pre_register(mcs, name, bases, attrs):
        """
        Pre-register hook.
        :param name: class name.
        :param bases: class bases.
        :param attrs: class attributes.
        :return: Modified tuple (name, bases, attrs)
        """
        return name, bases, attrs

    @classmethod
    def post_register(mcs, cls, name, bases, attrs):
        """
        Post-register hook.
        :param cls: created class.
        :param name: class name.
        :param bases: class bases.
        :param attrs: class attributes.
        :return: None.
        """

    def __new__(mcs, name, bases, attrs):
        """
        This method creates and registers new class, if it's not already
        in the register.
        """
        # Do not register the base classes, which actual classes inherit.
        if mcs.inherit_fields:
            for base in bases:
                for field, value in mcs.get_fields_from_base(base):
                    if field not in attrs:
                        attrs[field] = value
        if not attrs.get('__abstract__', False):
            missing = mcs.get_missing_fields(mcs.required_fields, attrs)
            if missing:
                raise RestEasyException(
                    'The following mandatory fields are missing from {} class definition: {}'.format(
                        name,
                        ', '.join(missing)
                    )
                )
            name, bases, attrs = mcs.pre_register(name, bases, attrs)
            slug = mcs.get_name(name, bases, attrs)
            cls = super(RegisteredCreator, mcs).__new__(mcs, name, bases, attrs)
            mcs.register.register(slug, cls)
            mcs.post_register(cls, name, bases, attrs)
        else:
            cls = super(RegisteredCreator, mcs).__new__(mcs, name, bases, attrs)
        return cls
