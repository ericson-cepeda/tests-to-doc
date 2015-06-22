#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

class Config(object):
    """ Configuration class for json Config"""

    def __init__(self, file_name):
        try:
            with open(file_name) as config_file:
                config = json.load(config_file)
                for key, value in config.items():
                    exec('self.%s = value' % (key,))
        except Exception as e:
            print(e)
