.. _usage:

Usage
=====

Generating Code and Infrastructure Configuration
------------------------------------------------

To only generate the Lambda function code and Terraform configuration, run:

.. code-block:: bash

    $ webhook2lambda2sqs generate

Note that when applying the configuration outside of ``webhook2lambda2sqs`` (i.e. using terraform directly), the
``api_gateway_method_settings`` configuration key will be ignored. See :ref:`method-settings`.

**Note** that the generated Terraform is a single file and does not make use of
variables. As Terraform doesn't support iteration or conditionals, it's really
required that we generate the important parts of the configuration programmatically,
so there's little use in ``tfvars``.

Managing Infrastructure
+++++++++++++++++++++++

``webhook2lambda2sqs`` provides ``plan``, ``apply`` and ``destroy`` commands which
wrap Terraform runs to perform those actions on the generated configuration. There is
also a ``genapply`` command to generate the Lambda Function and Terraform configuration,
and then apply it all in one command.

You'll want to have the ``AWS_DEFAULT_REGION`` environment variable set. AWS
credentials are managed however you want per `terraform's documentation <https://www.terraform.io/docs/providers/aws/index.html>`_, i.e. environment variables, shared credentials
file or using an instance profile/role on an EC2 instance.

**Important Note:** Unlike CloudFormation, Terraform relies on storing the
`state <https://www.terraform.io/docs/state/index.html>`_ of your managed infrastructure
itself. You can use a variety of `remote <https://www.terraform.io/docs/state/remote/index.html>`_
storage options including Consul, etcd, http and S3, or you can leave the default
of storing state locally in a ``terraform.tfstate`` file. Please note that you'll
need to save state somewhere in order to update or destroy the infrastructure you
created. You can specify remote state options in the configuration file, or just
deal with the state file locally.

AWS Resources Created
+++++++++++++++++++++

The following AWS resources are created by this program, when using a relatively
default configuration:

* 2 IAM Roles (the role used by API Gateway to invoke the Lambda Function, and the role used by the Lambda Function itself)
* 2 IAM Role Policy Attachments, one for each of those roles
* 1 API Gateway ReST API
* 1 Lambda Function
* 2 API Gateway Integration Responses for each method type (GET or POST) used
* 1 API Gateway Deployment
* 2 API Gateway Models

And for each endpoint in the configuration file:

* 2 API Gateway Method Responses for each configured endpoint
* An API Gateway Resource for each configured endpoint
* An API Gateway Integration for each configured endpoint
* An API Gateway Method for each configured endpoint

Estimated Cost of Infrastructure
++++++++++++++++++++++++++++++++

The following provides a cost estimate of the infrastructure as of August 6,
2016 in the US-East region. Please use the links below to find updated pricing
information.

* `Lambda Function <https://aws.amazon.com/lambda/pricing/>`_

  * First 1 million Lambda requests per month are free; $0.20 per million after that.

  * Compute time is charged at $0.000000208 per 100ms, with the first 3,200,000
    seconds free (this function runs with the default minimum of 128MB memory). Casual
    testing shows that this function, when pushing to one queue, should execute in 100-1100ms.

* `API Gateway <https://aws.amazon.com/api-gateway/pricing/>`_

  * $3.50 per million API calls (first 1 million per month are free for the first 12 months)
  * $0.09/GB for the first 10 TB of data transfer

Required IAM Permissions For Code Generation
--------------------------------------------

Generating the Terraform configuration files requires the ``iam::GetUser``
permission for the user you're running it as. This is required to determine
your AWS account ID, which is needed in the IAM policy. In addition, the region
that you connect with will be included in the policy.

Required IAM Permissions For Infrastructure Management and Querying
-------------------------------------------------------------------

Managing the infrastructure via Terraform, and using the AWS helper actions (
such as ``queuepeek``, ``logs`` and ``apilogs``) requires the following IAM
permissions: ::

    apigateway:CreateDeployment
    apigateway:CreateModel
    apigateway:CreateResource
    apigateway:CreateRestApi
    apigateway:DeleteIntegration
    apigateway:DeleteIntegrationResponse
    apigateway:DeleteMethod
    apigateway:DeleteMethodResponse
    apigateway:DeleteModel
    apigateway:DeleteResource
    apigateway:DeleteRestApi
    apigateway:DeleteStage
    apigateway:GetDeployment
    apigateway:GetIntegration
    apigateway:GetIntegrationResponse
    apigateway:GetMethod
    apigateway:GetMethodResponse
    apigateway:GetModel
    apigateway:GetResource
    apigateway:GetResources
    apigateway:GetRestApi
    apigateway:GetRestApis
    apigateway:GetStage
    apigateway:PutIntegration
    apigateway:PutIntegrationResponse
    apigateway:PutMethod
    apigateway:PutMethodResponse
    apigateway:UpdateStage
    iam:CreateRole
    iam:DeleteRole
    iam:DeleteRolePolicy
    iam:GetRole
    iam:GetRolePolicy
    iam:GetUser
    iam:ListInstanceProfilesForRole
    iam:PutRolePolicy
    lambda:CreateFunction
    lambda:DeleteFunction
    lambda:GetFunction
    lambda:UpdateFunctionCode
    lambda:UpdateFunctionConfiguration
    logs:DescribeLogGroups
    logs:DescribeLogStreams
    logs:GetLogEvents
    sqs:DeleteMessage
    sqs:GetQueueAttributes
    sqs:GetQueueUrl
    sqs:ListQueues
    sqs:ReceiveMessage
