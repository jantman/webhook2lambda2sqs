"""
The latest version of this package is available at:
<http://github.com/jantman/webhook2lambda2sqs>

################################################################################
Copyright 2016 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of webhook2lambda2sqs, also known as webhook2lambda2sqs.

    webhook2lambda2sqs is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    webhook2lambda2sqs is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with webhook2lambda2sqs.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/webhook2lambda2sqs> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import logging

logger = logging.getLogger(__name__)


class LambdaFuncGenerator(object):

    def __init__(self, config):
        """
        Initialize the Lambda function code generator.

        :param config: program configuration
        :type config: :py:class:`~.Config`
        """
        self.config = config

    def generate(self):
        """
        Generate Lambda function source; return it as a string.

        :rtype: str
        :returns: lambda function source
        """
        return """

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logger.debug('loaded function')

def webhook2lambda2sqs_handler(event, context):
    logger.debug('Event: %s', event)
    try:
        logger.debug('Context: %s', vars(context))
    except:
        logger.error('Error dumping context vars', excinfo=1)

        """
