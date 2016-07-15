webhook2lambda2sqs
========================

.. image:: https://pypip.in/v/webhook2lambda2sqs/badge.png
   :target: https://crate.io/packages/webhook2lambda2sqs

.. image:: https://pypip.in/d/webhook2lambda2sqs/badge.png
   :target: https://crate.io/packages/webhook2lambda2sqs

.. image:: https://secure.travis-ci.org/jantman/webhook2lambda2sqs.png?branch=master
   :target: http://travis-ci.org/jantman/webhook2lambda2sqs
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/webhook2lambda2sqs/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/webhook2lambda2sqs?branch=master
   :alt: coverage report for master branch

.. image:: http://www.repostatus.org/badges/latest/wip.svg
   :alt: Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.
   :target: http://www.repostatus.org/#wip

Generate code and manage infrastructure for receiving webhooks with AWS API Gateway and pushing to SQS via Lambda.

Webhooks are great, and many projects and services are now offering them as a notification option. But sometimes
it makes more sense to have the messages in a queue that can absorb changes in rate and de-couple the sending
 service from a potentially slow or unavailable backend.

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

Requirements
------------

* An Amazon AWS account to run this all in (note - it will probably be cheap, but not free)
* Python 2.7+ (currently tested with 2.7, 3.3, 3.4, 3.5). Note that AWS Lambda currently only supports python 2.7 as an execution environment, but you're welcome to use other versions on the machine where you run this project.
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `HashiCorp Terraform <https://www.terraform.io/>`_ to manage the AWS infrastructure, if desired. Terraform is written in Go,  and `distributed <https://www.terraform.io/downloads.html>`_ as a static binary.

Architecture
------------

Program Components
++++++++++++++++++

* Lambda Function code generation
* Terraform configuration generation
* Management of infrastructure via Terraform

AWS Components
++++++++++++++

* An IAM Role that allows the Lambda function to send messages to the specified SQS queues.
* The Lambda Function itself
* An API Gateway instance to receive webhooks and trigger the Lambda Function for them
* Optionally, a user-specified "vanity" Route53 DNS record pointing to the API Gateway

Installation
------------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv. If you really want to install
system-wide, you can (using sudo).

.. code-block:: bash

    pip install webhook2lambda2sqs

If you wish to use Terraform to manage the infrastructure, you need to install that
according to the `documentation <https://www.terraform.io/intro/getting-started/install.html>`_.
Note that there are packages available in the official repositories of most Linux
distributions, and there is also a Homebrew formula for Mac users.

Configuration
-------------

webhook2lambda2sqs is configured via a JSON configuration file, which defines both
settings for Terraform to manage the infrastructure, as well as the mapping of API
Gateway URL paths to SQS queues.

Usage
-----

Generating Code and Infrastructure Configuration
++++++++++++++++++++++++++++++++++++++++++++++++

Something else here.

Managing Infrastructure
+++++++++++++++++++++++

Something else here.

Bugs and Feature Requests
-------------------------

Bug reports and feature requests are happily accepted via the `GitHub Issue Tracker <https://github.com/jantman/webhook2lambda2sqs/issues>`_. Pull requests are
welcome. Issues that don't have an accompanying pull request will be worked on
as my time and priority allows.

Development
===========

To install for development:

1. Fork the `webhook2lambda2sqs <https://github.com/jantman/webhook2lambda2sqs>`_ repository on GitHub
2. Create a new branch off of master in your fork.

.. code-block:: bash

    $ virtualenv webhook2lambda2sqs
    $ cd webhook2lambda2sqs && source bin/activate
    $ pip install -e git+git@github.com:YOURNAME/webhook2lambda2sqs.git@BRANCHNAME#egg=webhook2lambda2sqs
    $ cd src/webhook2lambda2sqs

The git clone you're now in will probably be checked out to a specific commit,
so you may want to ``git checkout BRANCHNAME``.

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)

Testing
-------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off master for that issue.
2. Confirm that there are CHANGES.rst entries for all major changes.
3. Ensure that Travis tests passing in all environments.
4. Ensure that test coverage is no less than the last release (ideally, 100%).
5. Increment the version number in webhook2lambda2sqs/version.py and add version and release date to CHANGES.rst, then push to GitHub.
6. Confirm that README.rst renders correctly on GitHub.
7. Upload package to testpypi:

   * Make sure your ~/.pypirc file is correct (a repo called ``test`` for https://testpypi.python.org/pypi)
   * ``rm -Rf dist``
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist bdist_wheel``
   * ``twine upload -r test dist/*``
   * Check that the README renders at https://testpypi.python.org/pypi/webhook2lambda2sqs

8. Create a pull request for the release to be merged into master. Upon successful Travis build, merge it.
9. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a vX.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin vX.Y.Z``

11. Upload package to live pypi:

    * ``twine upload dist/*``

10. make sure any GH issues fixed in the release were closed.

A Note About the License
------------------------

This program is licensed under the `GNU Affero General Public License, version 3.0 or later <https://www.gnu.org/licenses/agpl-3.0.en.html>`_ ("AGPLv3").
The AGPLv3 includes a clause that source code must be made available to anyone using the program over a network.
