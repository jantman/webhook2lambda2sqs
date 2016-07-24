"""
NOTE: this file just serves as a template for the lambda function; it's read
in and transformed by
:py:meth:`webhook2lambda2sqs.func_generator.LambdaFuncGenerator._get_source`

This file should not be modified directly.
"""

import logging
import boto3
import json
from pprint import pformat
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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
    # be sure we log full information about any error
    try:
        res = handle_event(event, context)
    except Exception as ex:
        # log the error and re-raise the exception
        logger.error('Error handling event; event=%s context=%s',
                     event, vars(context), exc_info=1)
        raise ex
    if len(res['SQSMessageIds']) < 1:
        raise Exception('Failed enqueueing all messages.')
    return res


def handle_event(event, context):
    global endpoints
    logger.debug('Endpoint Config: %s; Event: %s; Context: %s',
                 pformat(endpoints), pformat(event), pformat(vars(context)))
    ep_name = event['context']['resource-path'].lstrip('/')
    if ep_name not in endpoints:
        raise Exception('Endpoint not in configuration: /%s' % ep_name)
    ep_conf = endpoints[ep_name]
    msg_ids = []
    failed = 0
    conn = boto3.client('sqs')
    msg = json.dumps({
        'event': serializable_dict(event),
        'context': serializable_dict(vars(context))
    })
    for queue_name in ep_conf['queues']:
        try:
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
            msg_ids.append(resp['MessageId'])
        except Exception:
            failed += 1
            logger.error('Failed enqueueing message in %s: %s', queue_name,
                         msg, exc_info=1)
    fail_str = ''
    if failed > 0:
        fail_str = '; %d failed' % failed
    return {
        'status': 'success',
        'message': 'enqueued %s messages%s' % (len(msg_ids), fail_str),
        'SQSMessageIds': msg_ids
    }


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
            # unserializable
            pass
    return newd
