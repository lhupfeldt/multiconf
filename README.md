[![Build Status](https://api.travis-ci.org/lhupfeldt/multiconf.svg?branch=master)](https://travis-ci.org/lhupfeldt/multiconf)
[![Documentation Status](https://readthedocs.org/projects/multiconf/badge/?version=stable)](https://multiconf.readthedocs.org/en/stable/)

What
====

Multiconf is a framework for describing complex configuration for multiple environments using Python.

Why?
===

It started from a simple need of deployment automation for Java EE projects, Apache and more. Having worked on different projects with plain text property files or XML configuration files, I thought something better was needed. With plain text property files, the number of property files increases as projects and environments are added, and number of scripts increases too. It gets hard to get an overview of properties describing similar configurations. Has a property value been defined for all projects for every environment? And it is getting even harder to describe *proper* settings: what depends on what and what can be used and what can't. With XML you keep having to extend the schema and the tool processing it. So why use XML or property files when you can have your configuration directly in python? So, out of this Multiconf was born.

What are proper settings?
------------------------

* All configured ports follow one convention
* All servers names follow one convention
* Some configuration objects must have mandatory parameters (for example: Database name or URL required for Datasource object)
* Some configuration objects must have mandatory children (for example: WebLogic Cluster doesn't make sense w/o Managed Servers)
* Default settings are propagated through all environments and can be overridden for specific environments
* No duplicated settings

How
===

Imagine that you have a project, where you are going to use Jboss and WebLogic. You are going to use database connections. And a project will typically have at least four environments: DevLocal (for developer's local machine), Dev (integration), Test and Prod, sometimes many more. The project configuration will be similar on different environments, but something will be different (databases, host names, number of hosts, number of WebLogic/Jboss servers,  and ports, for example).

What Multiconf is
=================

Multiconf provides a set of classes, where attributes may have different values for different environments, while enforcing that a value is defined for all defined environments.
Multiconf allows you to implement your own DOM like object model and get early warning that something within your definition is wrong. Other tools use YAML or JSON to define settings of the components, but then you need something to validate those settings. Multiconf is both - definition and validation.
Multiconf allows you to define environment groups, so that you can easily create new environments by adding them to a group and only override the values that differ from the group values.

What Multiconf is not
=====================

* Multiconf itself doesn't know how to create environments.
* Multiconf is not tied to configuration of any particular product or technology.
* Multiconf doesn't know how to create any of the environment's components
* Multiconf has nothing to execute

Running the demo:
=====================
Execute ./demo/demo.py --env <env> (or 'python demo/demo.py ...'), e.g:

  ./demo/demo.py --env prod

If run without args it will print a usage message
The valide environments are those specified at the top of demo/config.py

Running the test suite:
=====================
Execute: make, py.test or tox
Running 'make' will execute the test suite, the demo and build the documentation.

Requirements
=====================
Multiconf: Python 2.7.3+, Python 3.5+
Test Suite: pytest, pytest-cov, demjson (optional)
 - pip install -U pytest pytest-cov demjson
