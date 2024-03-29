#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import unittest
from unittest.mock import Mock, patch

from airflow.models import Connection
from airflow.models.dag import DAG
from airflow.providers.atlassian.jira.sensors.jira import JiraTicketSensor
from airflow.utils import db, timezone

DEFAULT_DATE = timezone.datetime(2017, 1, 1)
jira_client_mock = Mock(name="jira_client_for_test")


class _MockJiraTicket(dict):
    class _TicketFields:
        labels = ["test-label-1", "test-label-2"]
        description = "this is a test description"

    fields = _TicketFields


minimal_test_ticket = _MockJiraTicket(
    {
        "id": "911539",
        "self": "https://sandbox.localhost/jira/rest/api/2/issue/911539",
        "key": "TEST-1226",
    }
)


class TestJiraSensor(unittest.TestCase):
    def setUp(self):
        args = {'owner': 'airflow', 'start_date': DEFAULT_DATE}
        dag = DAG('test_dag_id', default_args=args)
        self.dag = dag
        db.merge_conn(
            Connection(
                conn_id='jira_default',
                conn_type='jira',
                host='https://localhost/jira/',
                port=443,
                extra='{"verify": "False", "project": "AIRFLOW"}',
            )
        )

    @patch("airflow.providers.atlassian.jira.hooks.jira.JIRA", autospec=True, return_value=jira_client_mock)
    def test_issue_label_set(self, jira_mock):
        jira_mock.return_value.issue.return_value = minimal_test_ticket

        ticket_label_sensor = JiraTicketSensor(
            method_name='issue',
            task_id='search-ticket-test',
            ticket_id='TEST-1226',
            field='labels',
            expected_value='test-label-1',
            timeout=518400,
            poke_interval=10,
            dag=self.dag,
        )

        ticket_label_sensor.run(start_date=DEFAULT_DATE, end_date=DEFAULT_DATE, ignore_ti_state=True)

        assert jira_mock.called
        assert jira_mock.return_value.issue.called
