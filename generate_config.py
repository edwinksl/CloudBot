#!/usr/bin/env python

import json
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

IRC_HOST = os.environ['IRC_HOST']
IRC_USER = os.environ['IRC_USER']
IRC_PASS = os.environ['IRC_PASS']
IRC_PORT = int(os.environ['IRC_PORT'])

with open('config.default.json') as f:
    data = json.load(f)

data_0 = data['connections'][0]
data_0['name'] = IRC_USER
data_0['connection']['server'] = IRC_HOST
data_0['connection']['port'] = IRC_PORT
data_0['connection']['ssl'] = True
data_0['connection']['ignore_cert'] = False
data_0['connection']['password'] = IRC_PASS
data_0['nick'] = IRC_USER
data_0['user'] = IRC_USER
data_0['channels'] = []
data_0['permissions']['admins']['users'] = []
data_0['permissions']['moderators']['users'] = []

data['web']['bot_name'] = IRC_USER

with open('config.json', 'w') as f:
    json.dump(data, f, indent=4)
    f.write('\n')
