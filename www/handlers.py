#!/usr/bin/env python3
#-*- coding:utf-8 -*-
''

__author__ = 'kaishuibaicai'

from models import User, Comment, Blog, next_id
from coroweb import get, post # 导入装饰器，这样就能方便的生成request handler
import re, time, json, logging, hashlib, base64, asyncio


@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__' : 'test.html',
        'users' : users
    }
