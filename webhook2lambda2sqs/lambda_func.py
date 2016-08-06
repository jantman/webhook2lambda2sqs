"""
NOTE: this file just serves as a template for the lambda function; it's read
in and transformed by
:py:meth:`webhook2lambda2sqs.func_generator.LambdaFuncGenerator._get_source`

This file should not be modified directly.
"""

import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# suppress boto3 internal logging below WARNING level
boto3_log = logging.getLogger("boto3")
boto3_log.setLevel(logging.WARNING)
boto3_log.propagate = True

# suppress botocore internal logging below WARNING level
botocore_log = logging.getLogger("botocore")
botocore_log.setLevel(logging.WARNING)
botocore_log.propagate = True

# suppress requests internal logging below WARNING level
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = True

endpoints = {}


def webhook2lambda2sqs_handler(event, context):
    """
    Main entry point/handler for the lambda function. Wraps
    :py:func:`~.handle_event` to ensure that we log detailed information if it
    raises an exception.

    :param event: Lambda event that triggered the handler
    :type event: dict
    :param context: Lambda function context - see
      http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    :return: JSON-serialized success response
    :rtype: str
    :raises: Exception
    """
    # be sure we log full information about any error; if handle_event()
    # raises an exception, log a bunch of information at error level and then
    # re-raise the Exception
    try:
        res = handle_event(event, context)
    except Exception as ex:
        # log the error and re-raise the exception
        logger.error('Error handling event; event=%s context=%s',
                     event, vars(context), exc_info=1)
        raise ex
    logger.debug('handle_event() result: %s', res)
    # if all enqueues failed, this should be an error
    if len(res['SQSMessageIds']) < 1:
        raise Exception('Failed enqueueing all messages')
    # if success, return the success JSON response
    return res


def queues_for_endpoint(event):
    """
    Return the list of queues to publish to for a given endpoint.

    :param event: Lambda event that triggered the handler
    :type event: dict
    :return: list of queues for endpoint
    :rtype: list
    :raises: Exception
    """
    global endpoints  # endpoint config that's templated in by generator
    # get endpoint config
    try:
        ep_name = event['context']['resource-path'].lstrip('/')
        return endpoints[ep_name]['queues']
    except:
        raise Exception('Endpoint not in configuration: /%s' % ep_name)


def msg_body_for_event(event, context):
    """
    Generate the JSON-serialized message body for an event.

    :param event: Lambda event that triggered the handler
    :type event: dict
    :param context: Lambda function context - see
      http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    :return: JSON-serialized success response
    :rtype: str
    """
    # find the actual input data - this differs between GET and POST
    http_method = event.get('context', {}).get('http-method', None)
    if http_method == 'GET':
        data = event.get('params', {}).get('querystring', {})
    else:  # POST
        data = event.get('body-json', {})
    # build the message to enqueue
    msg_dict = {
        'data': serializable_dict(data),
        'event': serializable_dict(event),
        'context': serializable_dict(vars(context))
    }
    msg = json.dumps(msg_dict, sort_keys=True)
    logger.debug('Message to enqueue: %s', msg)
    return msg


def handle_event(event, context):
    """
    Do the actual event handling - try to enqueue the request.

    :param event: Lambda event that triggered the handler
    :type event: dict
    :param context: Lambda function context - see
      http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    :return: JSON-serialized success response
    :rtype: str
    :raises: Exception
    """
    queues = queues_for_endpoint(event)
    # store some state
    msg_ids = []
    failed = 0
    # get the message to enqueue
    msg = msg_body_for_event(event, context)
    # connect to SQS API
    conn = boto3.client('sqs')
    for queue_name in queues:
        try:
            msg_ids.append(try_enqueue(conn, queue_name, msg))
        except Exception:
            failed += 1
            logger.error('Failed enqueueing message in %s:', queue_name,
                         exc_info=1)
    fail_str = ''
    status = 'success'
    if failed > 0:
        fail_str = '; %d failed' % failed
        status = 'partial'
    return {
        'status': status,
        'message': 'enqueued %s messages%s' % (len(msg_ids), fail_str),
        'SQSMessageIds': msg_ids
    }


def try_enqueue(conn, queue_name, msg):
    """
    Try to enqueue a message. If it succeeds, return the message ID.

    :param conn: SQS API connection
    :type conn: :py:class:`botocore:SQS.Client`
    :param queue_name: name of queue to put message in
    :type queue_name: str
    :param msg: JSON-serialized message body
    :type msg: str
    :return: message ID
    :rtype: str
    """
    logger.debug('Getting Queue URL for queue %s', queue_name)
    qurl = conn.get_queue_url(QueueName=queue_name)['QueueUrl']
    logger.debug('Sending message to queue at: %s', qurl)
    resp = conn.send_message(
        QueueUrl=qurl,
        MessageBody=msg,
        DelaySeconds=0
    )
    logger.debug('Enqueued message in %s with ID %s', queue_name,
                 resp['MessageId'])
    return resp['MessageId']


def serializable_dict(d):
    """
    Return a dict like d, but with any un-json-serializable elements removed.
    """
    newd = {}
    for k in d.keys():
        if isinstance(d[k], type({})):
            newd[k] = serializable_dict(d[k])
            continue
        try:
            json.dumps({'k': d[k]})
            newd[k] = d[k]
        except:
            pass  # unserializable
    return newd
