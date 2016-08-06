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
import sys
import pytest
import requests
import boto3
import json
from pprint import pformat

from webhook2lambda2sqs.utils import pretty_json

acceptance_config = {
    'api_gateway_method_settings': {
        'metricsEnabled': True,
        'loggingLevel': 'INFO',
        'dataTraceEnabled': True,
        'throttlingBurstLimit': 123,
        'throttlingRateLimit': 100.0
    },
    'deployment_stage_name': 'mystage',
    'endpoints': {
        'goodQueue': {
            'method': 'POST',
            'queues': ['w2l2sitest1']
        },
        'goodGetQueue': {
            'method': 'GET',
            'queues': ['w2l2sitest2']
        },
        'badQueue': {
            'method': 'GET',
            'queues': ['f3f0823u8uf']
        },
        'badQueuePost': {
            'method': 'POST',
            'queues': ['f3f0823u8uf']
        },
        'oneGoodQueueOneBad': {
            'method': 'POST',
            'queues': ['w2l2sitest2', 'f3f0823u8uf']
        }
    },
    'logging_level': 'DEBUG',
    'name_suffix': 'integrtest'
}


@pytest.mark.acceptance
class TestAccpetance(object):

    def get_message_id(self, queuename, run_id, method_name):
        """
        Return True if the queue has a matching message, False otherwise.
        """
        conn = boto3.client('sqs')
        qurl = conn.get_queue_url(QueueName=queuename)['QueueUrl']
        # we want to get ALL messages in the queue
        seen_ids = []
        all_msgs = []
        empty_polls = 0
        # continue getting messages until we get 2 empty polls in a row
        while empty_polls < 2:
            msgs = conn.receive_message(
                QueueUrl=qurl,
                MaxNumberOfMessages=10,
                VisibilityTimeout=240,
                WaitTimeSeconds=20
            )
            if 'Messages' in msgs and len(msgs['Messages']) > 0:
                empty_polls = 0
                print("Queue %s - got %d messages" % (
                    queuename, len(msgs['Messages'])))
                for m in msgs['Messages']:
                    if m['MessageId'] in seen_ids:
                        continue
                    seen_ids.append(m['MessageId'])
                    all_msgs.append(m)
                    conn.delete_message(
                        QueueUrl=qurl, ReceiptHandle=m['ReceiptHandle'])
                continue
            # no messages found
            print('Queue %s - got no messages' % queuename)
            empty_polls += 1
        print("Queue %s - %d messages:" % (queuename, len(all_msgs)))
        for m in all_msgs:
            j = json.loads(m['Body'])
            if ('data' not in j or 'method' not in j['data'] or
                    'run_id' not in j['data']):
                print("=> Queue %s: %s - non-matching message:\n%s" % (
                    queuename, m['MessageId'], pretty_json(j)
                ))
                continue
            print("=> Queue %s: %s - method=%s run_id=%s" % (
                queuename, m['MessageId'],
                j['data']['method'], j['data']['run_id']))
            if (j['data']['method'] == method_name and
                    j['data']['run_id'] == run_id):
                return m['MessageId']
        return None

    def _request(self, method, url, data):
        sys.stderr.write("\n%s %s (data: %s)\n" % (method, url, data))
        if method == 'GET':
            return requests.get(url, params=data)
        return requests.post(url, json=data)

    def test_aaa(self, acceptance_fixture):
        """dirty hack to clean up test output"""
        assert 0 == 0

    def test_method_settings(self, acceptance_fixture):
        api_id, base_url, run_id = acceptance_fixture
        conn = boto3.client('apigateway')
        stage = conn.get_stage(restApiId=api_id, stageName='mystage')
        assert 'methodSettings' in stage, 'Stage: %s' % pformat(stage)
        assert '*/*' in stage['methodSettings'], 'Stage: %s' % pformat(stage)
        settings = stage['methodSettings']['*/*']
        conf = acceptance_config['api_gateway_method_settings']
        for k in conf:
            assert k in settings, 'Stage: %s' % pformat(stage)
            assert settings[k] == conf[k], 'Stage: %s' % pformat(stage)

    def test_post_queue_ok(self, acceptance_fixture):
        api_id, base_url, run_id = acceptance_fixture
        url = base_url + 'goodQueue/'
        meth_name = '%s.%s.%s' % (__name__, self.__class__.__name__,
                                  sys._getframe().f_code.co_name)
        r = self._request('POST', url, {
            'run_id': run_id,
            'method': meth_name
        })
        print('Response (%d) content: %s' % (r.status_code, r.text))
        resp = r.json()
        print('Response JSON: %s' % resp)
        assert r.status_code == 202
        assert resp['status'] == 'success'
        assert 'SQSMessageIds' in resp
        assert len(resp['SQSMessageIds']) == 1
        msg = self.get_message_id('w2l2sitest1', run_id, meth_name)
        assert msg == resp['SQSMessageIds'][0]

    def test_get_queue_ok(self, acceptance_fixture):
        api_id, base_url, run_id = acceptance_fixture
        url = base_url + 'goodGetQueue/'
        meth_name = '%s.%s.%s' % (__name__, self.__class__.__name__,
                                  sys._getframe().f_code.co_name)
        r = self._request('GET', url, {
            'run_id': run_id,
            'method': meth_name
        })
        print('Response (%d) content: %s' % (r.status_code, r.text))
        resp = r.json()
        print('Response JSON: %s' % resp)
        assert r.status_code == 202
        assert resp['status'] == 'success'
        assert 'SQSMessageIds' in resp
        assert len(resp['SQSMessageIds']) == 1
        msg = self.get_message_id('w2l2sitest2', run_id, meth_name)
        assert msg == resp['SQSMessageIds'][0]

    def test_get_bad_queue(self, acceptance_fixture):
        api_id, base_url, run_id = acceptance_fixture
        url = base_url + 'badQueue/'
        meth_name = '%s.%s.%s' % (__name__, self.__class__.__name__,
                                  sys._getframe().f_code.co_name)
        r = self._request('GET', url, {
            'run_id': run_id,
            'method': meth_name
        })
        print('Response (%d) content: %s' % (r.status_code, r.text))
        resp = r.json()
        print('Response JSON: %s' % resp)
        assert r.status_code == 500
        assert resp['status'] == 'error'
        assert 'SQSMessageIds' not in resp
        assert self.get_message_id('w2l2sitest1', run_id, meth_name) is None
        assert self.get_message_id('w2l2sitest2', run_id, meth_name) is None

    def test_post_bad_queue(self, acceptance_fixture):
        api_id, base_url, run_id = acceptance_fixture
        url = base_url + 'badQueuePost/'
        meth_name = '%s.%s.%s' % (__name__, self.__class__.__name__,
                                  sys._getframe().f_code.co_name)
        r = self._request('POST', url, {
            'run_id': run_id,
            'method': meth_name
        })
        print('Response (%d) content: %s' % (r.status_code, r.text))
        resp = r.json()
        print('Response JSON: %s' % resp)
        assert r.status_code == 500
        assert resp['status'] == 'error'
        assert 'SQSMessageIds' not in resp
        assert self.get_message_id('w2l2sitest1', run_id, meth_name) is None
        assert self.get_message_id('w2l2sitest2', run_id, meth_name) is None

    def test_post_one_good_one_bad(self, acceptance_fixture):
        api_id, base_url, run_id = acceptance_fixture
        url = base_url + 'oneGoodQueueOneBad/'
        meth_name = '%s.%s.%s' % (__name__, self.__class__.__name__,
                                  sys._getframe().f_code.co_name)
        r = self._request('POST', url, {
            'run_id': run_id,
            'method': meth_name
        })
        print('Response (%d) content: %s' % (r.status_code, r.text))
        resp = r.json()
        print('Response JSON: %s' % resp)
        assert r.status_code == 202
        assert resp['status'] == 'partial'
        assert resp['message'] == 'enqueued 1 messages; 1 failed'
        assert len(resp['SQSMessageIds']) == 1
        assert self.get_message_id('w2l2sitest1', run_id, meth_name) is None
        msg = self.get_message_id('w2l2sitest2', run_id, meth_name)
        assert msg == resp['SQSMessageIds'][0]
