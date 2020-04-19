# yamaha-firmware-notify ![CI on Push](https://github.com/inokappa/yamaha-firmware-notify/workflows/CI%20on%20Push/badge.svg)

## About

* YAMAHA ネットワーク機器のファームウェア更新情報を Slack チャンネルに通知する Lambda 関数です
* 更新情報は有志の方が開設されている https://rtxpro.com/?feed=rss2 を利用させて頂きました

## Workflow

![sequence dialog](http://www.plantuml.com/plantuml/proxy?src=https://gist.githubusercontent.com/inokappa/711c9bc07ac27ab9026746d0233a3d70/raw/b169ed1455e17835f21aac5c48ac450711715803/flow.txt)

_https://gist.github.com/inokappa/711c9bc07ac27ab9026746d0233a3d70_

## Required

* [Serverless Framework](https://serverless.com)
* [serverless-python-requirements](https://github.com/UnitedIncome/serverless-python-requirements#readme)

## Deploy

### Install serverless plugin

```sh
$ sls plugin install -n serverless-python-requirements
```

### Set `Slack Webhook URL` to ssm parameter store

```sh
$ pstore -put \
  -name=your-parameter-name \
  -value=https://hooks.slack.com/services/XXXXXXXXX/YYYYYYYYYYY/xxxxxxxxxxxxxxxxxxxxxxxxxxx -secure
```

Please use [pstore](https://github.com/oreno-tools/pstore) command.

### Write env-dev.yml

```yaml
SLACK_CHANNEL: "#your-slack-channel"
SLACK_USERNAME: "YAMAHA Firmware Release Check"
SLACK_ICON_EMOJI: ":police_car:"
FIRMWARE_RELEASE_URL: "https://rtxpro.com/?feed=rss2"
YAMAHA_URL: "http://www.rtpro.yamaha.co.jp/RT/firmware/"
SSM_PARAMETER_NAME: "your-parameter-name"
MACHINES: "RTX1200,WLX402,SWX2210-8G" # Set the name of your Yamaha network device,
DYNAMODB_TABLE: "yamaha-firmware-notify"
```

### Run sls deploy

```sh
$ sls deploy --stage=dev
```

## Example

![image](https://github.com/inokappa/yamaha-firmware-notify/blob/master/docs/2020041701.png?raw=true)

## Test

### Run docker container

```sh
$ docker-compose build
$ docker-compose up -d
```

### Set up dependencies

```sh
$ docker exec -t -i --rm myservice bash
bash-5.0# pip install -r requirements.txt
```

or

```sh
$ docker-compose exec myservice pip install -r requirements.txt
```

### Run test

```sh
bash-5.0# pytest --verbose --disable-warnings test_handler.py
```

or

```sh
$ docker-compose exec myservice pytest --verbose --disable-warnings test_handler.py
```
