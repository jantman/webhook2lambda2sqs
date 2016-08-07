.. _http_responses:

HTTP Responses
==============

The API Gateway methods respond with a JSON object including ``status``,
``request_id`` (API Gateway Request ID) and ``message`` fields. If any messages
were successfully enqueued, the SQS MessageIds will be available in a
``SQSMessageIds`` list. Successful, or partially successful requests get a 202
response code, and complete failures get a 500 response code.

Completely successful response
------------------------------

.. code-block:: json

    {
      "status" : "success",
      "message" : "enqueued 1 messages",
      "SQSMessageIds": ["0720e7b5-8a81-4258-ba6c-afd69bcf60f6"],
      "request_id": "37af7edd-5bf2-11e6-9dcf-19b7d04d8b74"
    }

Partially successful response
-----------------------------

.. code-block:: json

    {
      "status" : "partial",
      "message" : "enqueued 1 messages; 1 failed",
      "SQSMessageIds": ["549eda2f-b449-4e2a-908c-ab9bb4a8022d"],
      "request_id": "b11a1b6b-5bf2-11e6-8fdb-a3f21465c2f6"
    }

Failure response
----------------

.. code-block:: json

    {
      "status" : "error",
      "message" : "Exception: Failed enqueueing all messages",
      "request_id": "505e01a7-5bf2-11e6-91eb-adc915445063"
    }
