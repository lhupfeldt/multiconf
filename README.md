
What
====

Multiconf is a framework for describing complex environments using Python.

Why
===

It started from a simple need of deployment automation for J2EE projects. And it started as a bunch of Python scripts, and a bunch of plain text property files. When number of property files increased and number of scripts increased too. And then it was hard to get a hold of properties describing similar servers. And it was geetting even harder to describe *proper* settings: what depends on what and what can be used and what can't. So out of this pain Multionf was born.

What is proper settings?
------------------------

* All configured ports follow one convention
* All servers names follow one convention
* Some configuration objects must have mandatory parameters (for example: Database name or URL required for Datasource object)
* Some configuration objects must have mandatory children (for example: WebLogic Cluster doesn't make sense w/o Managed Servers)
* Default settings are propagated through all environments and can be overridden for specific environment
* No duplicated settings

How
===

Imagine that you have a project, where you are going to use Jboss and Weblogic. You are going to use database connections. And project will have four environments: DelLocal (for developer's local machine), Dev, Test and Prod. The project configuration will be similar on different environments, but something will be different (databases and ports, for example).

What Multiconf is not
=====================

* Multiconf itself doesn't know how to create environments.
* Multiconf doesn't know how to create any of the environment's components
* Multiconf have nothing to execute


What Multiconf is
=================

Multiconf allows you to define your software stack and get early warning that something within your definition is wrong. Other tools use YAML or JSON to define settings of the components, but then you need something to validate those settings. Multiconf is both - definition and validation.

