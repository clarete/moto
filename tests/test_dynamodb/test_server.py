'''
Test the different server responses
'''

from moto.testing import TestClient


def test_missing_request():
    # Given that I have a test http client
    test_client = TestClient('dynamodb')

    # When I hit the root url of the dynamo handler
    res = test_client.get('/')

    # Then I see that we just get a not-found, meh
    res.status_code.should.equal(404)


def test_table_list():
    # Given that I have a test http client
    test_client = TestClient('dynamodb')

    # When I hit the root url of the dynamo handler, sending the right headers
    headers = {'X-Amz-Target': 'TestTable.ListTables'}
    res = test_client.get('/', headers=headers)

    # Than I see that the request was successful
    res.data.should.contain('TableNames')
