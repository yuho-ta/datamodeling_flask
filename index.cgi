#!/usr/keio/Anaconda3-2023.09-0/bin/python

import cgitb
cgitb.enable()

from wsgiref.handlers import CGIHandler
import os
os.environ['SCRIPT_NAME'] = \
    os.environ['SCRIPT_NAME'].removesuffix('/index.cgi')

from app import app

CGIHandler().run(app)
