"""
NOTE: this file just serves as a template for the lambda function; it's read
in and transformed by
:py:meth:`webhook2lambda2sqs.func_generator.LambdaFuncGenerator._get_source`

This file should not be modified directly.
"""

import logging
from pprint import pformat
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

endpoints = {}


def webhook2lambda2sqs_handler(event, context):
    # be sure we log full information about any error
    try:
        return handle_event(event, context)
    except Exception as ex:
        # log the error and re-raise the exception
        logger.error('Error handling event; event=%s context=%s',
                     event, vars(context), exc_info=1)
        raise ex


def handle_event(event, context):
    global endpoints
    logger.debug('TYPES: event=%s, context=%s', type(event), type(context))
    logger.debug('Endpoint Config: %s', pformat(endpoints))
    logger.debug('Event: %s', pformat(event))
    try:
        logger.debug('Context: %s', pformat(vars(context)))
    except:
        logger.info('Error dumping context vars', excinfo=1)
    # DEBUG
    if event['body-json'] is not None and 'foo' in event['body-json']:
        if event['body-json']['foo'] == 'a':
            return {'status': 'success', 'message': 'mymsg'}
        elif event['body-json']['foo'] == 'b':
            return {'status': 'error', 'message': 'mymsg'}
        elif event['body-json']['foo'] == 'c':
            raise Exception('some exception')
        else:
            pass
    # END DEBUG
    return {'status': 'success', 'message': 'param foo not set'}
