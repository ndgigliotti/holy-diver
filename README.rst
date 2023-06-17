==========
holy-diver
==========


.. image:: https://img.shields.io/pypi/v/holy-diver.svg
        :target: https://pypi.python.org/pypi/holy-diver

``holy-diver`` is a Python library that provides a simple, dot-accessible configuration
manager, which especially handy for deeply nested configuration files.
It's named after the song "Holy Diver" by Dio, due to its divine usefulness for diving
deep into nested configuration data.
It offers some convenient features such handling default settings, checking for the
presence of required keys, and initializing directly from YAML, JSON, and TOML files.
It employs two main classes: ``Config`` and ``ConfigList``. ``Config`` is a
dictionary-like class that allows you to access nested keys using dot notation
(i.e. recursively accessing keys as if they were attributes). ``ConfigList`` is a list-like
class that allows you to access elements using indices and dot notation for nested keys.
Both classes work together in harmony to make it as easy as possible to manage deeply
nested configuration data.

Main Features
=============

- Easy-to-use API for managing configuration data
- Recursively dot-accessible dictionary-like ``Config`` class
- Recursively dot-accessible list-like ``ConfigList`` class
- Support for YAML, JSON, and TOML configuration file formats

Installation
============

To install holy-diver, simply run:

.. code-block:: bash

    pip install holy-diver

Usage
=====

Config
-------------

Here's a quick example of how to use the ``Config`` class. First create a
``Config`` object from a dictionary:

.. code-block:: python

    from holy_diver import Config

    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {
                "user": "admin",
                "password": "secret",
            },
        }
    }

    config = Config.from_dict(config_data)

Access nested keys attribute-style using dot notation:

.. code-block:: python

    print(config.database.host)  # Output: localhost
    print(config.database.port)  # Output: 5432

You can also set values using dot notation:

.. code-block:: python

    config.database.host = "impala.company.com"
    print(config.database.host)  # Output: impala.company.com

Alternatively, you can directly look up nested keys:

.. code-block:: python

    print(config["database.host"])  # Output: localhost
    print(config["database.port"])  # Output: 5432

And of course, you can access them the old fashioned way:

.. code-block:: python

    print(config["database"]["host"])  # Output: localhost
    print(config["database"]["port"])  # Output: 5432

ConfigList
-----------------

Here's a quick example of how to use the ``ConfigList`` class.
Items in ``ConfigList`` can be accessed using normal indexing and
dot notation interchangeably. All indices can be accessed entirely with dot notation,
which allows for easier handling of nested keys and data structures.

.. code-block:: python

    from holy_diver import ConfigList

    list_data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ]

    config_list = ConfigList.from_list(list_data)

Access elements using indices and dot notation for nested keys:

.. code-block:: python

    print(config_list[0].name)  # Output: Alice
    print(config_list[1].age)   # Output: 25

Or, do it all with dot notation, if you prefer:

.. code-block:: python

    print(config_list._0.name) # Output: Alice
    print(config_list._1.age)  # Output: 25

The leading underscore allows numeric indices to be accessed as attributes. The
leading underscore is always required for attribute access, but is optional in other
contexts. You can see all the nested keys using the ``deep_keys()`` method, which shows
the leading underscore for numeric indices:

.. code-block:: python

    print(config_list.deep_keys())
    # Output: ['_0', '_1', '_0.name', '_0.age', '_1.name', '_1.age']

You can also look up nested keys directly:

.. code-block:: python

    print(config_list["_0.name"]) # Output: Alice
    print(config_list["_1.age"])  # Output: 25

    # It also works without the underscore
    print(config_list["0.name"]) # Output: Alice
    print(config_list["1.age"])  # Output: 25

Loading from a Configuration File
---------------------------------

You can load a configuration file in YAML format using the ``Config.from_yaml()`` method:

.. code-block:: python

    from holy_diver import Config

    config = Config.from_yaml("config.yaml")

Loading a JSON file works in much the same way:

.. code-block:: python

    from holy_diver import Config

    config = Config.from_json("config.json")

Alternative Constructors
------------------------
It's generally recommended to use one of the ``from_*()`` constructors
(e.g. ``from_dict()``, ``from_yaml()``) to create either a ``Config``
or ``ConfigList``, because these class methods automatically
convert nested dictionaries and lists to manager classes. It shouldn't affect the
functionality much if you use the main constructor, but it may cost you a few
milliseconds of processing time down the road, as more conversions must be
performed on the fly.

Writing to a Configuration File
-------------------------------

You can dump the configuration in various formats: YAML, JSON, and TOML.
Simply use the corresponding ``to_*()`` method (e.g. ``to_yaml()``, ``to_json()``)
and supply a path. Note that ``ConfigList`` objects can only be dumped to
YAML and JSON.

Converting and Deconverting
---------------------------
If you want to, you can convert the entire hierarchy to nested managers using the
``convert()`` method. This is done automatically when using the ``from_*()`` constructors,
but if you've used the main constructor or added some keys and values (an odd thing to do),
you might want to obtain a converted copy of the hierarchy. Again, this has a barely noticeable
effect on the functionality. Alternatively, you can deconvert the hierarchy to nested dicts and
lists using the ``deconvert()`` method. This is useful if you want the configuration data
in vanilla Python data structures for serialization.

.. code-block:: python

    from holy_diver import Config

    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {
                "user": "admin",
                "password": "secret",
            },
        }
    }

    config = Config(config_data) # Create a manager using main constructor
    converted = config.convert() # Convert to nested managers
    deconverted = converted.deconvert() # Deconvert to nested dicts and lists

    # Access nested keys
    print(config.database.host)  # Output: localhost
    print(converted.database.host)  # Output: localhost
    print(deconverted["database"]["host"])  # Output: localhost


Setting Defaults
----------------
You can set default values for keys that may not be present in the configuration data.
Simply pass the ``defaults`` keyword argument to any of the ``Config`` constructors.
This argument should be a dictionary of default values. If a key is not present in the
configuration data, the default value will be used instead. The user configuration is recursively
merged with the defaults to ensure that nested keys are handled properly.

.. code-block:: python

    from holy_diver import Config

    default_config = {
        "database": {
            "host": "impala.megacorp.com", # Will be overridden
            "port": 21050, # Will be overridden
            "auth_method": "LDAP", # Not present in the config data
        }
    }
    config_data = {"database": {"host": "localhost", "port": 5432}}

    config = Config.from_dict(config_data, defaults=default_config)

    print(config.database.host)  # Output: localhost
    print(config.database.port) # Output: 5432
    print(config.database.auth_method)  # Output: LDAP


Checking for Required Keys
--------------------------
One of the nice features of ``Config`` is that it allows you to check for the presence of
required keys. This is especially useful because it works for nested keys using dot notation.

.. code-block:: python

    from holy_diver import Config

    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {
                "user": "admin",
                "password": "secret",
            },
        }
    }

    required_keys = ["database.host", "database.credentials.user", "database.auth_method"]

    config = Config.from_dict(config_data) # Create a manager

    config.check_required_keys(required_keys, if_missing="raise")
    # Output: KeyError: Configuration is missing required keys: ['database.auth_method']

Raise a warning instead of an exception by passing ``if_missing="warn"``:

.. code-block:: python

    missing_keys = config.check_required_keys(required_keys, if_missing="warn")
    # Output: UserWarning: Configuration is missing required keys: ['database.auth_method']
    print(missing_keys) # Output: ["database.auth_method"]

Or, quietly get a list of missing keys by passing ``if_missing="return"``:

.. code-block:: python

    missing_keys = config.check_required_keys(required_keys, if_missing="return")
    print(missing_keys) # Output: ["database.auth_method"]

You can also check for required keys by passing ``required_keys`` to any of the
``Config`` constructors.

.. code-block:: python

    config = Config.from_dict(config_data, required_keys=required_keys)
    # Output: KeyError: Configuration is missing required keys: ['database.auth_method']


Contributing
============

We appreciate your contributions to the project! Please submit a pull request or create an issue on the GitHub repository to contribute.

License
=======

``holy-diver`` is released under the MIT License. See the LICENSE file for more details.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage