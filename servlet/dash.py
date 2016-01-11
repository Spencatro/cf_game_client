#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, r'../servlet/')
sys.path.insert(0, r'..')
sys.path.insert(0, r'../lib/')
from dash_wsgi import app as application
application.secret_key = 'SUPER SECRET WAHAHA'
