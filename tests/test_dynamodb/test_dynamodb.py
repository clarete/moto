import boto
from freezegun import freeze_time
import requests

from moto import mock_dynamodb
from moto.dynamodb import dynamodb_backend

from boto.dynamodb import condition
from boto.exception import DynamoDBResponseError


@mock_dynamodb
def test_list_tables():
    # Given that I have a table in my dynamo backend
    name = 'TestTable'
    dynamodb_backend.create_table(name, hash_key_attr="name", hash_key_type="S")

    # When I use the boto API to list tables
    conn = boto.connect_dynamodb('the_key', 'the_secret')

    # Then I see the exact table I just created
    conn.list_tables().should.equal(['TestTable'])


@mock_dynamodb
def test_list_tables_layer_1():
    # Given that I have two tables in my dynamo backend
    dynamodb_backend.create_table("test_1", hash_key_attr="name", hash_key_type="S")
    dynamodb_backend.create_table("test_2", hash_key_attr="name", hash_key_type="S")

    # When I list tables with the limit flag set to 1
    conn = boto.connect_dynamodb('the_key', 'the_secret')
    res = conn.layer1.list_tables(limit=1)

    # Then I see that, as expected, I received the partial list of tables
    expected = {"TableNames": ["test_1"], "LastEvaluatedTableName": "test_1"}
    res.should.equal(expected)

    # And then I see that I can still retrieve the rest of the list using both
    # `limit` and `start_table`.
    res = conn.layer1.list_tables(limit=1, start_table="test_1")
    expected = {"TableNames": ["test_2"]}
    res.should.equal(expected)


@mock_dynamodb
def test_describe_missing_table():
    # Given that I have a working connection to my dynamo impl
    conn = boto.connect_dynamodb('the_key', 'the_secret')

    # When I call describe against a missing table; Then I see I get the
    # `DynamoDBResponseError`.
    conn.describe_table.when.called_with('messages').should.throw(DynamoDBResponseError)


@mock_dynamodb
def test_sts_handler():
    # When I post a request to the amazon sts handler
    res = requests.post("https://sts.amazonaws.com/", data={"GetSessionToken": ""})

    # Then I see that the connection worked and has the `SecretAccessKey`
    res.ok.should.be.ok
    res.text.should.contain("SecretAccessKey")


@mock_dynamodb
def test_dynamodb_with_connect_to_region():
    # this will work if connected with boto.connect_dynamodb()
    dynamodb = boto.dynamodb.connect_to_region('us-west-2')

    schema = dynamodb.create_schema('column1', str(), 'column2', int())
    dynamodb.create_table('table1', schema, 200, 200)
