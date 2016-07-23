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
import json
import os
import requests
import boto3

acceptance_config = {
    'endpoints': {
        'goodQueue': {
            'method': 'POST',
            'queues': ['w2l2sitest1']
        },
        'badQueue': {
            'method': 'GET',
            'queues': ['f3f0823u8uf']
        },
        'oneGoodQueueOneBad': {
            'method': 'POST',
            'queues': ['w2l2sitest2', 'f3f0823u8uf']
        }
    },
    'name_suffix': 'integrtest'
}


@pytest.mark.acceptance
class TestAccpetance(object):

    def queue_has_message(self, queuename, method, run_id, msg_id):
        """
        Return True if the queue has a matching message, False otherwise.
        """
        conn = boto3.client('sqs')

    def _request(self, method, url, data):
        sys.stderr.write("\n%s %s (data: %s)\n" % (method, url, data))
        if method == 'GET':
            return requests.get(url, params=data)
        return requests.post(url, json=data)

    def test_aaa(self, acceptance_fixture):
        """dirty hack to clean up test output"""
        assert 0 == 0

    def test_post_queue_ok(self, acceptance_fixture):
        base_url, run_id = acceptance_fixture
        url = base_url + 'goodQueue/'
        meth_name = '%s.%s.%s' % (__name__, self.__class__.__name__,
                                  sys._getframe().f_code.co_name)
        r = self._request('POST', url, {
            'run_id': run_id,
            'method': meth_name
        })
        assert r.status_code == 202
        resp = r.json()
        print('Response JSON: %s', resp)
        assert resp['status'] == 'success'
        assert 'SQSMessageIds' in resp

