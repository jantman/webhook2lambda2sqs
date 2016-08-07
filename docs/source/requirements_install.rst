.. _requirements_install:

Requirements and Installation
=============================

Requirements
------------

* An Amazon AWS account to run this all in (note - it will probably be cheap, but not free)
* Python 2.7+ (currently tested with 2.7, 3.3, 3.4, 3.5). Note that AWS Lambda currently only supports python 2.7 as an execution environment, but you're welcome to use other versions on the machine where you run this project.
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `HashiCorp Terraform <https://www.terraform.io/>`_ >= 0.6.16 to manage the AWS infrastructure, if desired. Terraform is written in Go,  and `distributed <https://www.terraform.io/downloads.html>`_ as a static binary.

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
