.. _queue_message_format:

Queue Message Format
====================

The lambda function will enqueue JSON messages in the SQS queue(s) containing
all information available to the function; namely, the ``event`` dictionary
describing the event that triggered the function and the
`context object <http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html>`_
(minus any un-serializable attributes) describing the execution environment.

Additionally, a top-level ``data`` key will be created in the message, containing
the POST data for POST requests or the parameters for GET requests.

GET
---

Example GET request against endpoint name ``other`` (configured to enqueue in
one queue) of ReST API ID ``hc0zenxxs1``, with configuration parameter
``deployment_stage_name`` set to ``hooks``:

.. code-block:: bash

   $ curl -i 'https://hc0zenxxs1.execute-api.us-east-1.amazonaws.com/hooks/other/?foo=bar&baz=blam'
   HTTP/1.1 202 Accepted
   Content-Type: application/json
   Content-Length: 190
   Connection: keep-alive
   Date: Sat, 06 Aug 2016 16:59:22 GMT
   x-amzn-RequestId: 1df19527-5bf7-11e6-9962-f9b69e643a7f
   X-Cache: Miss from cloudfront
   Via: 1.1 33ca1aa308d2c3dd926101c0bb80980a.cloudfront.net (CloudFront)
   X-Amz-Cf-Id: pXs73XR10oo6yzAjcopq0c6ZNYGNF3NntEVKAyVFp2HdcEsRikCqtQ==

   {
     "status" : "success",
     "message" : "enqueued 1 messages",
     "SQSMessageIds": ["74219fc5-99cb-4f07-8e86-df4793ebe2ee"],
     "request_id": "1df19527-5bf7-11e6-9962-f9b69e643a7f"
   }

Message enqueued for that request (MessageId ``74219fc5-99cb-4f07-8e86-df4793ebe2ee``):

.. code-block:: json

    {
        "context": {
            "aws_request_id": "1dfd7bb5-5bf7-11e6-960b-f76084d997b6",
            "client_context": null,
            "function_name": "webhook2lambda2sqs",
            "function_version": "$LATEST",
            "invoked_function_arn": "arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:function:webhook2lambda2sqs",
            "log_group_name": "/aws/lambda/webhook2lambda2sqs",
            "log_stream_name": "2016/08/06/[$LATEST]1c9be741f09e489b852d6f0932e5d15c",
            "memory_limit_in_mb": "128"
        },
        "data": {
            "baz": "blam",
            "foo": "bar"
        },
        "event": {
            "body-json": {},
            "context": {
                "account-id": "",
                "api-id": "hc0zenxxs1",
                "api-key": "",
                "authorizer-principal-id": "",
                "caller": "",
                "cognito-authentication-provider": "",
                "cognito-authentication-type": "",
                "cognito-identity-id": "",
                "cognito-identity-pool-id": "",
                "http-method": "GET",
                "request-id": "1df19527-5bf7-11e6-9962-f9b69e643a7f",
                "resource-id": "dpc2fo",
                "resource-path": "/other",
                "source-ip": "24.98.234.117",
                "stage": "hooks",
                "user": "",
                "user-agent": "curl/7.49.1",
                "user-arn": ""
            },
            "params": {
                "header": {
                    "Accept": "*/*",
                    "CloudFront-Forwarded-Proto": "https",
                    "CloudFront-Is-Desktop-Viewer": "true",
                    "CloudFront-Is-Mobile-Viewer": "false",
                    "CloudFront-Is-SmartTV-Viewer": "false",
                    "CloudFront-Is-Tablet-Viewer": "false",
                    "CloudFront-Viewer-Country": "US",
                    "Host": "hc0zenxxs1.execute-api.us-east-1.amazonaws.com",
                    "User-Agent": "curl/7.49.1",
                    "Via": "1.1 33ca1aa308d2c3dd926101c0bb80980a.cloudfront.net (CloudFront)",
                    "X-Amz-Cf-Id": "9_xjz8J2zxic_S9QUudB1k8oiw_0IoIlgLXqVKyzapSbg-AXcxEjIg==",
                    "X-Forwarded-For": "24.98.234.117, 216.137.42.113",
                    "X-Forwarded-Port": "443",
                    "X-Forwarded-Proto": "https"
                },
                "path": {},
                "querystring": {
                    "baz": "blam",
                    "foo": "bar"
                }
            },
            "stage-variables": {}
        }
    }

POST
----

Example POST request against endpoint name ``some_resource_name`` (configured to
enqueue in two queues) of ReST API ID ``hc0zenxxs1``, with configuration parameter
``deployment_stage_name`` set to ``hooks``:

.. code-block:: bash

   $ curl -i -X POST -H 'Content-Type: application/json' -d '{"foo": "bar", "baz": "blam"}' 'https://hc0zenxxs1.execute-api.us-east-1.amazonaws.com/hooks/some_resource_name/'
   HTTP/1.1 202 Accepted
   Content-Type: application/json
   Content-Length: 229
   Connection: keep-alive
   Date: Sat, 06 Aug 2016 17:07:11 GMT
   x-amzn-RequestId: 36a79c5a-5bf8-11e6-928c-cf1c3c738a1d
   X-Cache: Miss from cloudfront
   Via: 1.1 5b1f6dfc9ebdbec2869a5bfa561dded0.cloudfront.net (CloudFront)
   X-Amz-Cf-Id: _Gpuo8bQJrn0Iniz5IsP4BurnCqUDEtLcsXFx1buoneNOYhxYprOUg==


   {
     "status" : "success",
     "message" : "enqueued 2 messages",
     "SQSMessageIds": ["6bf3600d-2734-4b31-bed3-c996a0290e09","c29320f7-3687-4652-b0f4-ffea02052ea2"],
     "request_id": "36a79c5a-5bf8-11e6-928c-cf1c3c738a1d"
   }

Message enqueued for that request (MessageId ``6bf3600d-2734-4b31-bed3-c996a0290e09``):

.. code-block:: json

    {
        "context": {
            "aws_request_id": "36b30df4-5bf8-11e6-a360-8be4c8dc98ef",
            "client_context": null,
            "function_name": "webhook2lambda2sqs",
            "function_version": "$LATEST",
            "invoked_function_arn": "arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:function:webhook2lambda2sqs",
            "log_group_name": "/aws/lambda/webhook2lambda2sqs",
            "log_stream_name": "2016/08/06/[$LATEST]1c9be741f09e489b852d6f0932e5d15c",
            "memory_limit_in_mb": "128"
        },
        "data": {
            "baz": "blam",
            "foo": "bar"
        },
        "event": {
            "body-json": {
                "baz": "blam",
                "foo": "bar"
            },
            "context": {
                "account-id": "",
                "api-id": "hc0zenxxs1",
                "api-key": "",
                "authorizer-principal-id": "",
                "caller": "",
                "cognito-authentication-provider": "",
                "cognito-authentication-type": "",
                "cognito-identity-id": "",
                "cognito-identity-pool-id": "",
                "http-method": "POST",
                "request-id": "36a79c5a-5bf8-11e6-928c-cf1c3c738a1d",
                "resource-id": "mgaaye",
                "resource-path": "/some_resource_name",
                "source-ip": "24.98.234.117",
                "stage": "hooks",
                "user": "",
                "user-agent": "curl/7.49.1",
                "user-arn": ""
            },
            "params": {
                "header": {
                    "Accept": "*/*",
                    "CloudFront-Forwarded-Proto": "https",
                    "CloudFront-Is-Desktop-Viewer": "true",
                    "CloudFront-Is-Mobile-Viewer": "false",
                    "CloudFront-Is-SmartTV-Viewer": "false",
                    "CloudFront-Is-Tablet-Viewer": "false",
                    "CloudFront-Viewer-Country": "US",
                    "Content-Type": "application/json",
                    "Host": "hc0zenxxs1.execute-api.us-east-1.amazonaws.com",
                    "User-Agent": "curl/7.49.1",
                    "Via": "1.1 5b1f6dfc9ebdbec2869a5bfa561dded0.cloudfront.net (CloudFront)",
                    "X-Amz-Cf-Id": "cFDJLUHTujRZpIKnCtFhklW5XI3vMU7mz7ADpg52J5R5Mqklo4-hdg==",
                    "X-Forwarded-For": "24.98.234.117, 216.137.42.98",
                    "X-Forwarded-Port": "443",
                    "X-Forwarded-Proto": "https"
                },
                "path": {},
                "querystring": {}
            },
            "stage-variables": {}
        }
    }
