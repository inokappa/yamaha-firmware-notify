import pytest
import boto3
import base64

from moto import mock_dynamodb2
from moto import mock_ssm

from handler import *


class TestHandler:
    def setup_method(self, method):
        print('SetUp')

    def teardown_method(self, method):
        print('Teardown')

    def test_generate_keystring(self):
        enc_message = generate_keystring('foo', 'bar')
        decoded = base64.b64decode(enc_message.encode('ascii'))
        assert decoded.decode('ascii') == 'foo+bar'

    @mock_dynamodb2
    def test_write_table(self):
        dynamodb = boto3.client('dynamodb', region_name='ap-northeast-1')
        dynamodb.create_table(
            TableName='yamaha-firmware-notify',
            KeySchema=[
                {
                    'AttributeName': 'key',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'key',
                    'AttributeType': 'S'
                }
            ]
        )
        enc_message = generate_keystring('RTX1200', 'Rev.10.01.78')
        result = write_table(enc_message, 'RTX1200', 'Rev.10.01.78')
        assert True is result

    @mock_dynamodb2
    def test_write_table_revision_already_exists(self):
        dynamodb = boto3.client('dynamodb', region_name='ap-northeast-1')
        dynamodb.create_table(
            TableName='yamaha-firmware-notify',
            KeySchema=[
                {
                    'AttributeName': 'key',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'key',
                    'AttributeType': 'S'
                },
            ]
        )
        enc_message = generate_keystring('RTX1200', 'Rev.10.01.78')
        item = {
            'key': {'S': enc_message},
            'machine': {'S': 'RTX1200'},
            'revision': {'S': 'Rev.10.01.78'},
        }
        dynamodb.put_item(TableName='yamaha-firmware-notify', Item=item)
        result = write_table(enc_message, 'RTX1200', 'Rev.10.01.78')
        assert False is result

    @mock_ssm
    def test_get_ssm_parameter(self):
        ssm = boto3.client('ssm', region_name='ap-northeast-1')
        ssm.put_parameter(Name='test', Value='string', Type='SecureString')

        result = get_ssm_parameter('test')
        assert 'string' == result['Parameter']['Value']

    @mock_ssm
    def test_get_ssm_parameter_not_exists(self):
        ssm = boto3.client('ssm', region_name='ap-northeast-1')
        ssm.put_parameter(Name='test', Value='string', Type='SecureString')

        result = get_ssm_parameter('test1')
        assert '' == result
