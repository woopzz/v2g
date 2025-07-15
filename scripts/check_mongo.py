#!/usr/bin/env python3
from pymongo import MongoClient

client = MongoClient(host='mongo', port=27017)
print('ping result =', client.admin.command('ping'))
