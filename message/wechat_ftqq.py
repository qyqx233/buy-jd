#!/usr/bin/env python
# -*- encoding=utf8 -*-
import datetime

import orjson
import aiohttp.client_exceptions
from log.jdlogger import logger
from util.http import get_raw


async def sendWechat(sc_key, text='京东商品监控', desp=''):
    if not text.strip():
        logger.error('Text of message is empty!')
        return

    now_time = str(datetime.datetime.now())
    desp = '[{0}]'.format(now_time) if not desp else '{0} [{1}]'.format(desp, now_time)

    try:
        resp = await get_raw(
            'https://sc.ftqq.com/{}.send?text={}&desp={}'.format(sc_key, text, desp)
        )
        resp_json = orjson.loads(resp.text)
        if resp_json.get('errno') == 0:
            logger.info('Message sent successfully [text: %s, desp: %s]', text, desp)
        else:
            logger.error('Fail to send message, reason: %s', resp.text)
    except aiohttp.client_exceptions.ClientError as req_error:
        logger.error('Request error: %s', req_error)
    except Exception as e:
        logger.error('Fail to send message [text: %s, desp: %s]: %s', text, desp, e)
