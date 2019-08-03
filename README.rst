|Build Status| |Coverage| |Documentation Status| |PyPi Package|

What
====

Multiconf is a framework for describing a complex configuration for
multiple environments using Python.

Why?
====

It started from a simple need of deployment automation for Java EE projects,
Apache and more. Having worked on different projects with nested levels of
plain text property files or XML configuration files,I thought something
better was needed.
With plain text property files, the number of property files increases as
environments and technologies are added to a project. It becomes hard to get
an overview of properties describing similar configurations. Has a property
value been defined for every environment? And it is getting even harder to
describe *proper* settings: what depends on what and what can be used and what
can't.
With XML on the other hand, you can create a strict validated model, but you
keep having to extend the schema and the tools processing it. And maybe you
don't like the verbosity.
So why use XML or property files when you can have your configuration directly
in python? So, out of this Multiconf was born.

What are proper settings?
-------------------------

E.g:

-  All configured ports follow one convention
-  All servers names follow one convention
-  Some configuration objects must have mandatory parameters (for
   example: Database name or URL required for Datasource object)
-  Some configuration objects must have mandatory children (for example:
   WebLogic Cluster doesn't make sense w/o Managed Servers)
-  Default settings are propagated through all environments and can be
   overridden for specific environments
-  No duplicated settings

How
===

Multiconf provides a set of classes, where attributes may have different
values for different environments, while enforcing that a value is
defined for all defined environments. Multiconf allows you to implement
your own DOM like object model and get early warning that something
within your definition is wrong. Other tools use YAML or JSON to define
settings of the components, but then you need something to validate
those settings. Multiconf is both - definition and validation. Multiconf
allows you to define environment groups, so that you can easily create
new environments by adding them to a group and only override the values
that differ from the group values.

You have to define your configuration data model as classes derived from
Multiconf base classes, one of which is ``ConfigItem``.

E.g, in your config data model (your framework) you define:

.. code:: python

    class Host(ConfigItem):
        def __init__(name=MC_REQUIRED, mem=MC_REQUIRED):
            self.name = name
            self.mem = mem

        @property
        def fqd(self):
            return "{name}.{env}.my.organisation".format(
                self.name, self.env.name)

In you project configuration file you can then declare a configuration object
with different attribute values for different environments:

.. code:: python

    ...
    with Host("web1") as host:
        host.setattr('mem', dev="1G", tst="2G", preprod="4G", prod="4G")

Above uses the Multiconf ``setattr`` method to assign different values to different
envs. Note that the envs *dev*, *tst*, *preprod* and *prod* must have been declared
beforehand and Multiconf will ensure that all of them get a value.

After instantiating your config for the *prod* env you can then access
properties on the host object::

    cfg.host.name -> web1
    cfg.host.mem -> 4G
    cfg.host.fqd -> web1.prod.my.organisation

Note that classes derived from the Multiconf classes (e.g: ``ConfigItem``) do not
allow on the fly creation of attributes. Configuration items are not meant for
general programming, but for strictly validated configurations.

See the documentation and the *demo* project for details about nested objects,
repeatable objects, instantiation, environment definitions, environment groups,
default values and other details.
    

What Multiconf is not
=====================

-  Multiconf is not tied to configuration of any particular product or
   technology.
-  Multiconf doesn't know how to create any of the environment's
   components, i.e. Multiconf has no 'playbooks' or 'recipes' to execute.


Running the demo:
=================

Execute ./demo/demo.py --env (or 'python demo/demo.py ...'), e.g:

./demo/demo.py --env prod

If run without any arguments it will print a usage message The valid
environments are those specified at the top of demo/config.py

Running the test suite:
=======================

Execute: make, py.test or tox Running 'make' will execute the test
suite, the demo and build the documentation.

Requirements
============

Multiconf: Python 3.6.1+ Test Suite: pytest, pytest-cov (for older Python versions use multiconf 8.x)
demjson (optional) - pip install -U pytest pytest-cov demjson

.. |Build Status| image:: https://api.travis-ci.org/lhupfeldt/multiconf.svg?branch=master
   :target: https://travis-ci.org/lhupfeldt/multiconf
.. |Documentation Status| image:: https://readthedocs.org/projects/multiconf/badge/?version=stable
   :target: https://multiconf.readthedocs.org/en/stable/
.. |PyPi Package| image:: https://badge.fury.io/py/multiconf.svg
   :target: https://badge.fury.io/py/multiconf
.. |Coverage| image:: https://coveralls.io/repos/github/lhupfeldt/multiconf/badge.svg?branch=master
   :target: https://coveralls.io/github/lhupfeldt/multiconf?branch=master
.. |License| image:: https://img.shields.io/github/license/lhupfeldt/multiconf.svg
   :target: https://github.com/lhupfeldt/multiconf/blob/master/LICENSE.TXT
