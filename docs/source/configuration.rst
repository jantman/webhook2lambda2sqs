.. _configuration:

Configuration
=============

webhook2lambda2sqs is configured via a JSON configuration file, which defines both
settings for Terraform to manage the infrastructure, as well as the mapping of API
Gateway URL paths to SQS queues. You can view a sample configuration file as well
as documentation on the various fields with ``webhook2lambda2sqs example-config``;
the config file example will be written to STDOUT (so it may be redirected to a
file) and the documentation will be written to STDERR.

Example output of the ``example-config`` action::

    $ webhook2lambda2sqs example-config
    {
        "api_gateway_method_settings": {
            "dataTraceEnabled": false,
            "loggingLevel": "OFF",
            "metricsEnabled": false,
            "throttlingBurstLimit": null,
            "throttlingRateLimit": null
        },
        "deployment_stage_name": "something",
        "endpoints": {
            "other_resource_path": {
                "method": "GET",
                "queues": [
                    "queueName2",
                    "queueName3"
                ]
            },
            "some_resource_path": {
                "method": "POST",
                "queues": [
                    "queueName1",
                    "queueName2"
                ]
            }
        },
        "logging_level": "INFO",
        "name_suffix": "something",
        "terraform_remote_state": {
            "backend": "backend_name",
            "config": {
                "option_name": "option_value"
            }
        }
    }

    Configuration description:

    api_gateway_method_settings - (optional) Dictionary of API Gateway Method
      settings to enable. See
      <https://docs.aws.amazon.com/apigateway/api-reference/resource/stage/#methodSettings>
      for upstream documentation. Due to a limitation
      in Terraform (https://github.com/hashicorp/terraform/issues/6612), these
      settings are applied by this program via the AWS API after Terraform has
      run; if you use this program to generate Terraform configurations and
      apply them yourself, these settings will have no effect. The following
      keys and values are supported:

      - 'metricsEnabled' - (boolean, default False) whether or not to enable
        CloudWatch metrics for the API.
      - 'loggingLevel' - (string, default "OFF") logging level to use for
        pushing API Gateway logs to CloudWatch Logs. Valid values are "OFF",
        "ERROR" or "INFO".
      - 'dataTraceEnabled' - (boolean, default False) whether to enable data
        trace logging to CloudWatch Logs for the API Gateway.
      - 'throttlingBurstLimit' - (integer, default None) API Gateway throttling
        burst limit - see:
        <http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html?icmpid=docs_apigateway_console>
        Omit to not set this option.
      - 'throttlingRateLimit' - (double, default None) API Gateway throttling
        rate limit (requests per second). See:
        http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html?icmpid=docs_apigateway_console
        Omit to not set this option.

    deployment_stage_name - (optional) String used as the name for the API
      Gateway Deployment Stage, which will be the beginning component of the
      URL path for the API Gateway
      (i.e. https://<api id>.execute-api.us-east-1.amazonaws.com/STAGE_NAME/).
      Defaults to "webhook2lambda2sqs".

    endpoints - dict describing each webhook endpoint to setup in API Gateway.
      - key is the API Gateway resource name (final component of the URL)
      - value is a dict with the following keys:
        - 'method' - HTTP method for API Gateway resource
        - 'queues' - list of SQS queue names to push request content to

    logging_level - the Python logging level (constant name) to set for the
      lambda function. Defaults to INFO. Currently the function only logs at
      ERROR and DEBUG levels.

    name_suffix - (optional) by default, all AWS resources will be named
      "webhook2lambda2sqs"; specify a suffix to add to that name here.

    terraform_remote_state - (optional) dict of Terraform remote state options.
      If specified, will call 'terraform remote config' before every terraform
      command to setup remote state storage. See:
      https://www.terraform.io/docs/state/remote/index.html

      Dict keys:
      - 'backend' - name of the terraform remote state backend to configure
      - 'config' - dict of backend configuration option name/value pairs

.. _method-settings:

Note About API Gateway Method Settings
--------------------------------------

Terraform `currently lacks support <https://github.com/hashicorp/terraform/issues/6612>`_
for setting the ``methodSettings`` on an API Gateway Stage. These settings are
used to control rate limiting as well as enable CloudWatch logs and metrics
for the API Gateway itself. Until Terraform adds support for this, if you specify
the ``api_gateway_method_settings`` configuration key, this program will apply
the relevant settings using the AWS API directly after the Terraform run is
complete.
