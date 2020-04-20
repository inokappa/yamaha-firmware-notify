import os
from base64 import b64decode
import boto3
from botocore.exceptions import ClientError
import requests
import bs4
import base64
import slackweb
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

region = os.environ['AWS_REGION']
slack_channel = os.environ['SLACK_CHANNEL']
slack_username = os.environ['SLACK_USERNAME']
slack_icon_emoji = os.environ['SLACK_ICON_EMOJI']
firmware_release_note_url = os.environ['FIRMWARE_RELEASE_URL']
yamaha_site_url = os.environ['YAMAHA_URL']
param_name = os.environ['SSM_PARAMETER_NAME']
machines = os.environ['MACHINES']
dynamodb_table = os.environ['DYNAMODB_TABLE']


def get_ssm_parameter(param_name):
    ssm = boto3.client('ssm', region_name=region)
    try:
        res = ssm.get_parameter(
            Name=param_name,
            WithDecryption=True
        )
        return res
    except ClientError as e:
        print('ssm get parameter error.')
        return ''


def handle_soup(text):
    return bs4.BeautifulSoup(text, "html.parser")


def get_revision(soup, title):
    desc = soup.find('title', string=title)
    rev = desc.find_next('description').getText().split('。')[-2].split()[-2]
    return rev


def parse_contents(res):
    soup = handle_soup(res.text)
    elems = soup.select('title')
    titles = list(map(lambda x: x.getText(), elems))
    return soup, titles


def generate_slack_message(title, rev):
    head = '<!here> %s.' % title
    foot = '更新作業を検討して下さい. 尚, この通知は %s の情報を利用しています.' % firmware_release_note_url
    message = '最新のリビジョンは %s です. 詳細は %s を確認して下さい' % (rev, yamaha_site_url)
    text = head + '\n```\n' + message + '\n```\n' + foot
    return text


def post_slack(text):
    endpoint = get_ssm_parameter(param_name)['Parameter']['Value']
    if endpoint == '':
        raise
    slack = slackweb.Slack(url=endpoint)
    slack.notify(text=text,
                 channel=slack_channel,
                 username=slack_username,
                 icon_emoji=slack_icon_emoji)


def write_table(key, machine, rev):
    dynamodb = boto3.client('dynamodb', region_name=region)

    try:
        dynamodb.put_item(
            TableName=dynamodb_table,
            Item={
                'key': {'S': key},
                'machine': {'S': machine},
                'revision': {'S': rev}
            },
            Expected={
                'key': {
                    'Exists': False
                }
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print('duplicate key')
            return False
        else:
            raise
    else:
        return True


def generate_keystring(machine, rev):
    message = '%s+%s' % (machine, rev)
    enc_message = base64.b64encode(message.encode('utf-8'))
    return enc_message.decode("ascii")


def handler(event, context):
    res = requests.get(firmware_release_note_url)
    res.raise_for_status()
    soup, titles = parse_contents(res)
    for machine in machines.split(','):
        for title in titles:
            if machine in title:
                rev = get_revision(soup, title)
                keystring = generate_keystring(machine, rev)
                if write_table(keystring, machine, rev):
                    text = generate_slack_message(title, rev)
                    post_slack(text)
                    print('Notified. machine: %s, revision: %s'
                          % (machine, rev))
                else:
                    print('Already notified. machine: %s,'
                          'revision: %s' % (machine, rev))
            else:
                print('Skip : "%s"' % title)
