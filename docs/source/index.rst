.. meta::
   :description: Description of your package here

webhook2lambda2sqs
==================

.. image:: https://img.shields.io/pypi/v/webhook2lambda2sqs.svg?maxAge=2592000
   :target: https://pypi.python.org/pypi/webhook2lambda2sqs
   :alt: pypi version

.. image:: http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/pypi-stats/webhook2lambda2sqs/per-month.svg
   :target: http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/pypi-stats/webhook2lambda2sqs/index.html
   :alt: PyPi downloads

.. image:: https://img.shields.io/github/forks/jantman/webhook2lambda2sqs.svg
   :alt: GitHub Forks
   :target: https://github.com/jantman/webhook2lambda2sqs/network

.. image:: https://img.shields.io/github/issues/jantman/webhook2lambda2sqs.svg
   :alt: GitHub Open Issues
   :target: https://github.com/jantman/webhook2lambda2sqs/issues

.. image:: https://secure.travis-ci.org/jantman/webhook2lambda2sqs.png?branch=master
   :target: http://travis-ci.org/jantman/webhook2lambda2sqs
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/webhook2lambda2sqs/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/webhook2lambda2sqs?branch=master
   :alt: coverage report for master branch

.. image:: https://readthedocs.org/projects/webhook2lambda2sqs/badge/?version=latest
   :target: https://readthedocs.org/projects/webhook2lambda2sqs/?badge=latest
   :alt: sphinx documentation for latest release

.. image:: https://badge.waffle.io/jantman/webhook2lambda2sqs.png?label=ready&title=Ready
   :target: https://waffle.io/jantman/webhook2lambda2sqs
   :alt: 'Stories in Ready'

.. image:: http://www.repostatus.org/badges/latest/wip.svg
   :alt: Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.
   :target: http://www.repostatus.org/#wip

Generate code and manage infrastructure for receiving webhooks with AWS API Gateway and pushing to SQS via Lambda.

Webhooks are great, and many projects and services are now offering them as a notification option. But sometimes
it makes more sense to have the messages in a queue that can absorb changes in rate and de-couple the sending service from a potentially slow or unavailable backend.

webhook2lambda2sqs generates code for an `AWS Lambda <https://aws.amazon.com/lambda/>`_ function
to receive webhook content via `API Gateway <https://aws.amazon.com/api-gateway/>`_ and push it
to an SQS queue, where it can be consumed as needed. It supports multiple endpoints via unique URL
paths (API Gateway resources), where content sent to each endpoint is pushed to one or more SQS
queues.

In addition, webhook2lambda2sqs includes a wrapper around HashiCorp Terraform to automate creation
and maintenance of all or part of the infrastructure required to operate this (the API Gateway
and its configuration, the Lambda function, the function's IAM role, etc.). If TerraForm isn't
a viable option for you to manage infrastructure with, you can use the generated configuration
(which maps quite closely to AWS API parameters) as a guide for manual management.

There are also helper commands to view the Lambda Function and API Gateway logs,
send a test message, and view the queue contents.

Program Components
------------------

* Lambda Function code generation
* Terraform configuration generation
* Management of infrastructure via Terraform
* AWS-related helpers for inspecting queues and logs, querying information, and
  enabling metrics/logging/rate limiting on the API Gateway.

Bugs and Feature Requests
-------------------------

Bug reports and feature requests are happily accepted via the `GitHub Issue Tracker <https://github.com/jantman/webhook2lambda2sqs/issues>`_. Pull requests are
welcome. Issues that don't have an accompanying pull request will be worked on
as my time and priority allows.

Contents
========

.. toctree::
   :maxdepth: 4

   Requirements and Installation <requirements_install>
   Configuration <configuration>
   Usage <usage>
   HTTP Responses <http_responses>
   Queue Message Format <queue_message_format>
   API <modules>
   Development <development>
   Changelog <changes>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
--------

webhook2lambda2sqs is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_. This shouldn't be much of a concern to most people.
