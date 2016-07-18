"""
NOTE: this file just serves as a template for the lambda function; it's read
in and transformed by
:py:meth:`webhook2lambda2sqs.func_generator.LambdaFuncGenerator._get_source`

This file should not be modified directly.
"""

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logger.debug('loaded function')

endpoints = {}


def webhook2lambda2sqs_handler(event, context):
    global endpoints
    logger.debug('Endpoint Config: %s', endpoints)
    logger.debug('Event: %s', event)
    try:
        logger.debug('Context: %s', vars(context))
    except:
        logger.info('Error dumping context vars', excinfo=1)
    return {'foo': 'bar'}
