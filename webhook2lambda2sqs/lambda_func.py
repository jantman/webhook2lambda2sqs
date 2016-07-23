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
    try:
        handle_event(event, context)
    except Exception:
        logger.error('Error handling event event=%s context=%s',
                     event, vars(context), exc_info=1)
        return {'status': 'error'}


def handle_event(event, context):
    global endpoints
    logger.debug('TYPES: event=%s, context=%s', type(event), type(context))
    logger.debug('Endpoint Config: %s', pformat(endpoints))
    logger.debug('Event: %s', pformat(event))
    try:
        logger.debug('Context: %s', pformat(vars(context)))
    except:
        logger.info('Error dumping context vars', excinfo=1)
    return {'status': 'success'}
