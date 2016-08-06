"""
Main application entry point / runner for webhook2lambda2sqs.

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

import pytest
import sys
import os
import logging
import json
import boto3
import time
import requests

from webhook2lambda2sqs.tests.test_acceptance import acceptance_config
from webhook2lambda2sqs.runner import main as runner_main
from webhook2lambda2sqs.config import Config
from webhook2lambda2sqs.terraform_runner import TerraformRunner

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import Mock  # noqa
else:
    from unittest.mock import Mock  # noqa

# suppress requests logging
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = True


@pytest.fixture(scope="session", autouse=True)
def acceptance_fixture(request):
    """
    Spin up an actual instance of this app, for use in acceptance tests.

    :param request: pytest config
    :type request: TestConfig::test_init
    :return:
    :rtype:
    """
    sys.stderr.write("\n")
    # don't do anything if we're not in an acceptance test environment
    if "'-m', 'acceptance'" not in str(request.config._origargs):
        sys.stderr.write(
            "\tnot running mongodb - not run with '-m acceptance'\n"
        )
        return None

    if 'TRAVIS' in os.environ or 'CI' in os.environ:
        sys.stderr.write("\tnot running acceptance tests in CI environment\n")
        return None

    dir_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..', 'acceptance_tf'
    ))
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    def acceptance_teardown():
        sys.stderr.write("\n\ttearing down acceptance environment...\n")
        tear_down_acceptance(dir_path)

    sys.stderr.write("\tstarting up acceptance environment...\n")
    try:
        api_id, base_url = set_up_acceptance(dir_path)
    except Exception as ex:
        tear_down_acceptance(dir_path)
        raise ex
    request.addfinalizer(acceptance_teardown)
    test_run_identifier = str(time.time())
    sys.stderr.write("\nSLEEPING 120s for API deployment to stabilize\n")
    time.sleep(120)
    sys.stderr.write("Sending requests to all endpoints...\n")
    hit_all_endpoints(base_url)
    sys.stderr.write("Sleeping 10s...\n")
    time.sleep(10)
    return api_id, base_url, test_run_identifier


def hit_all_endpoints(base_url):
    """
    Send 3 requests to each endpoint. Perhaps this will help prime the API.
    """
    for i in range(0, 3):
        for ep in acceptance_config['endpoints']:
            url = base_url + ep + '/'
            if acceptance_config['endpoints'][ep]['method'] == 'GET':
                requests.get(url, params={'foo': 'bar', 'warmup': 1})
            else:
                requests.post(url, params={'foo': 'bar', 'warmup': 1})


def tear_down_acceptance(dir_path):
    """
    Tear down the infrastructure from the acceptance tests.
    """
    if os.environ.get('NO_TEARDOWN', None) == 'true':
        sys.stderr.write("\tNOT tearing down acceptance environment.\n")
        sys.stderr.write("\tINFRASTRUCTURE STILL RUNNING (tf_dir=%s)\n" %
                         dir_path)
        return
    sys.stderr.write("\ttear_down_acceptance(%s)\n" % dir_path)
    delete_queues()
    os.chdir(dir_path)
    args = Mock(verbose=2, action='destroy', tf_path='terraform',
                config='config.json')
    sys.stderr.write("\trunning destroy\n")
    runner_main(args)


def set_up_acceptance(dir_path):
    """
    Set up the infrastructure from the acceptance tests.
    """
    sys.stderr.write("\tset_up_acceptance(%s)\n" % dir_path)
    conf_json = json.dumps(acceptance_config)
    create_queues()
    with open(os.path.join(dir_path, 'config.json'), 'w') as fh:
        fh.write(conf_json)
    os.chdir(dir_path)
    sys.stderr.write("\trunning genapply\n")
    args = Mock(verbose=2, action='genapply', tf_path='terraform',
                config='config.json')
    runner_main(args=args)
    # get base url
    api_id, base_url = get_base_url(dir_path)
    return api_id, base_url


def get_base_url(dir_path):
    """
    get the base url to the API
    """
    os.chdir(dir_path)
    conf = Config(os.path.join(dir_path, 'config.json'))
    tf_runner = TerraformRunner(conf, 'terraform')
    outs = tf_runner._get_outputs()
    return outs['rest_api_id'], outs['base_url']


def delete_queues(conn=None):
    """
    Delete the test SQS queues.
    """
    if conn is None:
        conn = boto3.client('sqs')
    for q in ['w2l2sitest1', 'w2l2sitest2']:
        try:
            qurl = conn.get_queue_url(QueueName=q)['QueueUrl']
            conn.delete_queue(QueueUrl=qurl)
            sys.stderr.write("\tdeleted SQS queue %s\n" % q)
        except:
            sys.stderr.write("\terror deleting SQS queue %s\n" % q)


def create_queues():
    """
    Create the test SQS queues.
    """
    conn = boto3.client('sqs')
    for q in ['w2l2sitest1', 'w2l2sitest2']:
        try:
            qurl = conn.get_queue_url(QueueName=q)['QueueUrl']
            conn.purge_queue(QueueUrl=qurl)
            sys.stderr.write("\tpurged existing SQS queue %s\n" % q)
        except:
            conn.create_queue(QueueName=q)
            sys.stderr.write("\tcreated SQS queue %s\n" % q)
