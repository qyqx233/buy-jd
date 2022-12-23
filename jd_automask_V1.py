# -*- coding=utf-8 -*-
"""
京东抢购口罩程序
通过商品的skuid、地区id抢购
"""
import asyncio
import aiohttp
import json
import math
import orjson
import requests, re, pickle
import random
import sys, os 
import time, datetime
import http.cookies
from bs4 import BeautifulSoup
from log.jdlogger import logger
from util.http import get_session
from typing import List, Dict

# from jdemail.jdEmail import sendMail
from message.message import Message  # 更新v3 方糖
from config.config import global_config
import configparser
import threading
import aiohttp.client_exceptions


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.46"
ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
timesleep = 1
g_cookie = None

config = configparser.ConfigParser()
message = Message('3')

"""
需要修改
"""
# cookies在单独文件中保存 通过扫二维码登陆获取并自动保存
# 简洁模式
pure = global_config.getRaw("config", "pure_mode")
pure_mode = False
if pure != "0":
    print("pure mode is on")
    pure_mode = True
# 最大检测商品线程数量
thread_max_nums = int(global_config.getRaw("config", "thread_max_nums"))
if thread_max_nums < 2:
    logger.error("config.ini文件中输入的thread_max_nums有误！最小为2！")
    sys.exit(1)
# 方糖微信推送的key  不知道的请看http://sc.ftqq.com/3.version
sc_key = global_config.getRaw("config", "sc_key")
# 推送方式 1（mail）或 2（wechat）
messageType = str(global_config.getRaw("config", "messageType"))
# cookies在单独文件中保存 通过扫二维码登陆获取并自动保存
# 有货通知 收件邮箱
mail = global_config.getRaw("config", "mail")
# 地区id
area = str(global_config.getRaw("config", "area")).replace("-", "_").replace(" ", "")
print(area)
# 商品id
skuidsString = global_config.getRaw("config", "skuids")
skuids = str(skuidsString).split(",")
logger.info("[" + str(len(skuids)) + "]个需要检测的商品")
# print(skuids)
if len(skuids[0]) == 0:
    logger.error(
        "请在config.ini文件中输入你的商品id！！不会请看教程.txt或访问https://github.com/rlacat/jd-automask"
    )
    sys.exit(1)
if area == "":
    logger.error(
        "请在config.ini文件中输入你的地区id，否则程序无法正常运行！！不会请看教程.txt或访问https://github.com/rlacat/jd-automask"
    )
    sys.exit(1)
"""
备用
"""

# eid
eid = global_config.getRaw("config", "eid")
fp = global_config.getRaw("config", "fp")
# 支付密码
payment_pwd = global_config.getRaw("config", "payment_pwd")

manual_cookies: Dict = {}


def restore_cookie():
    global g_cookie
    with open('cookie', 'rb') as f:
        g_cookie = requests.utils.cookiejar_from_dict(pickle.load(f))

def get_tag_value(tag, key="", index=0):
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(" \t\r\n")


def response_status(resp: aiohttp.ClientResponse):
    if resp.status != requests.codes.OK:
        print("Status: %u, Url: %s" % (resp.status, resp.url))
        return False
    return True


"""
for item in cookies_String.split(';'):
    name, value = item.strip().split('=', 1)
    # 用=号分割，分割1次
    manual_cookies[name] = value
    # 为字典cookies添加内容

cookiesJar = requests.utils.cookiejar_from_dict(manual_cookies, cookiejar=None, overwrite=True)
已更新为扫二维码获取
"""


async def validate_cookies():
    for flag in range(1, 3):
        if not await spider.check_login():
            if not await spider.login_by_QR():
                await message.send("【京东口罩监控服务已开启】", True)
                sys.exit(-1)


async def getUsername():
    userName_Url = (
        "https://passport.jd.com/new/helloService.ashx?callback=jQuery339448&_="
        + str(int(time.time() * 1000))
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Connection": "keep-alive",
    }
    async with get_session().get(userName_Url, allow_redirects=True, headers=headers) as resp:
        resultText = await resp.text()
        resultText = resultText.replace("jQuery339448(", "")
        resultText = resultText.replace(")", "")
        usernameJson = json.loads(resultText)
        logger.info("登录账号名称" + usernameJson["nick"])


"""
检查是否有货
"""


async def check_item_stock(item_url: str):
    async with get_session().get(item_url) as response:
        if await response.text().find("无货") > 0:
            return True
        else:
            return False


"""
取消勾选购物车中的所有商品
"""


async def cancel_select_all_cart_item():
    url = "https://cart.jd.com/cancelAllItem.action"
    data = {"t": 0, "outSkus": "", "random": random.random()}
    async with get_session().post(url, json=data, cookies=g_cookie) as resp:
        if resp.status != requests.codes.OK:
            logger.info("Status: %u, Url: %s" % (resp.status, resp.url))
            return False
    return True


"""
勾选购物车中的所有商品
"""


async def select_all_cart_item():
    url = "https://cart.jd.com/selectAllItem.action"
    data = {"t": 0, "outSkus": "", "random": random.random()}
    async with get_session().post(url, json=data) as resp:
        if resp.status!= requests.codes.OK:
            print("Status: %u, Url: %s" % (resp.status, resp.url))
            return False
    return True


"""
删除购物车选中商品
"""


async def remove_item():
    url = "https://cart.jd.com/batchRemoveSkusFromCart.action"
    data = {
        "t": 0,
        "null": "",
        "outSkus": "",
        "random": random.random(),
        "locationId": "19-1607-4773-0",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.37",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://cart.jd.com/cart.action",
        "Host": "cart.jd.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Encoding": "zh-CN,zh;q=0.9,ja;q=0.8",
        "Origin": "https://cart.jd.com",
        "Connection": "keep-alive",
    }
    async with get_session().post(url, json=data, headers=headers) as resp:
        logger.info("清空购物车")
        if resp.status != requests.codes.OK:
            print("Status: %u, Url: %s" % (resp.status, resp.url))
            return False
    return True


"""
购物车详情
"""


async def cart_detail():
    url = "https://cart.jd.com/cart_index"
    # url = "http://localhost:8000/post"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": ACCEPT,
        # "Referer": "https://order.jd.com/center/list.action",
        "Host": "cart.jd.com",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0", 
    }
    async with get_session().get(url, headers=headers, cookies=dict(g_cookie)) as resp:
        text_raw = await resp.read()
        soup = BeautifulSoup(text_raw, "html.parser")
        with open('cart_detail.html', 'wb') as fw:
            fw.write(text_raw)

    cart_detail = {}
    for item in soup.find_all(class_="item-item"):
        try:
            sku_id = item["skuid"]  # 商品id
        except Exception as e:
            logger.info("购物车中有套装商品，跳过")
            continue
        try:
            # 例如：['increment', '8888', '100001071956', '1', '13', '0', '50067652554']
            # ['increment', '8888', '100002404322', '2', '1', '0']
            item_attr_list = item.find(class_="increment")["id"].split("_")
            p_type = item_attr_list[4]
            promo_id = target_id = item_attr_list[-1] if len(item_attr_list) == 7 else 0

            cart_detail[sku_id] = {
                "name": get_tag_value(item.select("div.p-name a")),  # 商品名称
                "verder_id": item["venderid"],  # 商家id
                "count": int(item["num"]),  # 数量
                "unit_price": get_tag_value(item.select("div.p-price strong"))[
                    1:
                ],  # 单价
                "total_price": get_tag_value(item.select("div.p-sum strong"))[1:],  # 总价
                "is_selected": "item-selected" in item["class"],  # 商品是否被勾选
                "p_type": p_type,
                "target_id": target_id,
                "promo_id": promo_id,
            }
        except Exception as e:
            logger.error("商品%s在购物车中的信息无法解析，报错信息: %s，该商品自动忽略", sku_id, e)

    logger.info("购物车信息：%s", cart_detail)
    return cart_detail


"""
修改购物车商品的数量
"""


async def change_item_num_in_cart(sku_id, vender_id, num, p_type, target_id, promo_id):
    url = "https://cart.jd.com/changeNum.action"
    data = {
        "t": 0,
        "venderId": vender_id,
        "pid": sku_id,
        "pcount": num,
        "ptype": p_type,
        "targetId": target_id,
        "promoID": promo_id,
        "outSkus": "",
        "random": random.random(),
        # 'locationId'
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart",
        "Connection": "keep-alive",
    }
    async with get_session().post(url, json=data, headers=headers) as resp:
        return orjson.loads(resp.read())["sortedWebCartResult"]["achieveSevenState"] == 2


"""
添加商品到购物车
"""


async def add_item_to_cart(sku_id):
    url = "https://cart.jd.com/gate.action"
    payload = {
        "pid": sku_id,
        "pcount": 1,
        "ptype": 1,
    }
    async with get_session().get(url=url, params=payload) as resp:
        if "https://cart.jd.com/cart.action" in str(resp.url):  # 套装商品加入购物车后直接跳转到购物车页面
            result = True
        else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
            soup = BeautifulSoup(await resp.read(), "html.parser")
            result = bool(soup.select("h3.ftx-02"))  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]

    if result:
        logger.info("%s  已成功加入购物车", sku_id)
    else:
        logger.error("%s 添加到购物车失败", sku_id)


async def get_checkout_page_detail():
    """获取订单结算页面信息

    该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

    :return: 结算信息 dict
    """
    url = "http://trade.jd.com/shopping/order/getOrderInfo.action"
    # url = 'https://cart.jd.com/gotoOrder.action'
    payload = {
        "rid": str(int(time.time() * 1000)),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
        "Host": "trade.jd.com",
    }
    try:
        async with get_session().get(url=url, params=payload, headers=headers) as resp:
            if not response_status(resp):
                logger.error("获取订单结算页信息失败")
                return ""

            soup = BeautifulSoup(await resp.read(), "html.parser")
            risk_control = get_tag_value(soup.select("input#riskControl"), "value")

            order_detail = {
                "address": soup.find("span", id="sendAddr").text[
                    5:
                ],  # remove '寄送至： ' from the begin
                "receiver": soup.find("span", id="sendMobile").text[
                    4:
                ],  # remove '收件人:' from the begin
                "total_price": soup.find("span", id="sumPayPriceId").text[
                    1:
                ],  # remove '￥' from the begin
                "items": [],
            }

            logger.info("下单信息：%s", order_detail)
            return order_detail
    except aiohttp.client_exceptions.ClientError as e:
        logger.error("订单结算页面获取异常：%s" % e)
    except Exception as e:
        logger.error("下单页面数据解析异常：%s", e)
    return risk_control


async def submit_order(risk_control):
    """提交订单

    重要：
    1.该方法只适用于普通商品的提交订单（即可以加入购物车，然后结算提交订单的商品）
    2.提交订单时，会对购物车中勾选✓的商品进行结算（如果勾选了多个商品，将会提交成一个订单）

    :return: True/False 订单提交结果
    """
    url = "https://trade.jd.com/shopping/order/submitOrder.action"
    # js function of submit order is included in https://trade.jd.com/shopping/misc/js/order.js?r=2018070403091

    # overseaPurchaseCookies:
    # vendorRemarks: []
    # submitOrderParam.sopNotPutInvoice: false
    # submitOrderParam.trackID: TestTrackId
    # submitOrderParam.ignorePriceChange: 0
    # submitOrderParam.btSupport: 0
    # riskControl:
    # submitOrderParam.isBestCoupon: 1
    # submitOrderParam.jxj: 1
    # submitOrderParam.trackId:

    data = {
        "overseaPurchaseCookies": "",
        "vendorRemarks": "[]",
        "submitOrderParam.sopNotPutInvoice": "false",
        "submitOrderParam.trackID": "TestTrackId",
        "submitOrderParam.ignorePriceChange": "0",
        "submitOrderParam.btSupport": "0",
        "riskControl": risk_control,
        "submitOrderParam.isBestCoupon": 1,
        "submitOrderParam.jxj": 1,
        "submitOrderParam.trackId": "9643cbd55bbbe103eef18a213e069eb0",  # Todo: need to get trackId
        # 'submitOrderParam.eid': eid,
        # 'submitOrderParam.fp': fp,
        "submitOrderParam.needCheck": 1,
    }

    def encrypt_payment_pwd(payment_pwd):
        return "".join(["u3" + x for x in payment_pwd])

    if len(payment_pwd) > 0:
        data["submitOrderParam.payPassword"] = encrypt_payment_pwd(payment_pwd)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        "Host": "trade.jd.com",
    }

    try:
        async with get_session.post(url=url, json=data, headers=headers) as resp:
            resp_json = orjson.loads(await resp.read())

        # 返回信息示例：
        # 下单失败
        # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60123, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '请输入支付密码！'}
        # {'overSea': False, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'orderXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60017, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '您多次提交过快，请稍后再试'}
        # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60077, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '获取用户订单信息失败'}
        # {"cartXml":null,"noStockSkuIds":"xxx","reqInfo":null,"hasJxj":false,"addedServiceList":null,"overSea":false,"orderXml":null,"sign":null,"pin":"xxx","needCheckCode":false,"success":false,"resultCode":600157,"orderId":0,"submitSkuNum":0,"deductMoneyFlag":0,"goJumpOrderCenter":false,"payInfo":null,"scaleSkuInfoListVO":null,"purchaseSkuInfoListVO":null,"noSupportHomeServiceSkuList":null,"msgMobile":null,"addressVO":{"pin":"xxx","areaName":"","provinceId":xx,"cityId":xx,"countyId":xx,"townId":xx,"paymentId":0,"selected":false,"addressDetail":"xx","mobile":"xx","idCard":"","phone":null,"email":null,"selfPickMobile":null,"selfPickPhone":null,"provinceName":null,"cityName":null,"countyName":null,"townName":null,"giftSenderConsigneeName":null,"giftSenderConsigneeMobile":null,"gcLat":0.0,"gcLng":0.0,"coord_type":0,"longitude":0.0,"latitude":0.0,"selfPickOptimize":0,"consigneeId":0,"selectedAddressType":0,"siteType":0,"helpMessage":null,"tipInfo":null,"cabinetAvailable":true,"limitKeyword":0,"specialRemark":null,"siteProvinceId":0,"siteCityId":0,"siteCountyId":0,"siteTownId":0,"skuSupported":false,"addressSupported":0,"isCod":0,"consigneeName":null,"pickVOname":null,"shipmentType":0,"retTag":0,"tagSource":0,"userDefinedTag":null,"newProvinceId":0,"newCityId":0,"newCountyId":0,"newTownId":0,"newProvinceName":null,"newCityName":null,"newCountyName":null,"newTownName":null,"checkLevel":0,"optimizePickID":0,"pickType":0,"dataSign":0,"overseas":0,"areaCode":null,"nameCode":null,"appSelfPickAddress":0,"associatePickId":0,"associateAddressId":0,"appId":null,"encryptText":null,"certNum":null,"used":false,"oldAddress":false,"mapping":false,"addressType":0,"fullAddress":"xxxx","postCode":null,"addressDefault":false,"addressName":null,"selfPickAddressShuntFlag":0,"pickId":0,"pickName":null,"pickVOselected":false,"mapUrl":null,"branchId":0,"canSelected":false,"address":null,"name":"xxx","message":null,"id":0},"msgUuid":null,"message":"xxxxxx商品无货"}
        # {'orderXml': None, 'overSea': False, 'noStockSkuIds': 'xxx', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'cartXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 600158, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': {'oldAddress': False, 'mapping': False, 'pin': 'xxx', 'areaName': '', 'provinceId': xx, 'cityId': xx, 'countyId': xx, 'townId': xx, 'paymentId': 0, 'selected': False, 'addressDetail': 'xxxx', 'mobile': 'xxxx', 'idCard': '', 'phone': None, 'email': None, 'selfPickMobile': None, 'selfPickPhone': None, 'provinceName': None, 'cityName': None, 'countyName': None, 'townName': None, 'giftSenderConsigneeName': None, 'giftSenderConsigneeMobile': None, 'gcLat': 0.0, 'gcLng': 0.0, 'coord_type': 0, 'longitude': 0.0, 'latitude': 0.0, 'selfPickOptimize': 0, 'consigneeId': 0, 'selectedAddressType': 0, 'newCityName': None, 'newCountyName': None, 'newTownName': None, 'checkLevel': 0, 'optimizePickID': 0, 'pickType': 0, 'dataSign': 0, 'overseas': 0, 'areaCode': None, 'nameCode': None, 'appSelfPickAddress': 0, 'associatePickId': 0, 'associateAddressId': 0, 'appId': None, 'encryptText': None, 'certNum': None, 'addressType': 0, 'fullAddress': 'xxxx', 'postCode': None, 'addressDefault': False, 'addressName': None, 'selfPickAddressShuntFlag': 0, 'pickId': 0, 'pickName': None, 'pickVOselected': False, 'mapUrl': None, 'branchId': 0, 'canSelected': False, 'siteType': 0, 'helpMessage': None, 'tipInfo': None, 'cabinetAvailable': True, 'limitKeyword': 0, 'specialRemark': None, 'siteProvinceId': 0, 'siteCityId': 0, 'siteCountyId': 0, 'siteTownId': 0, 'skuSupported': False, 'addressSupported': 0, 'isCod': 0, 'consigneeName': None, 'pickVOname': None, 'shipmentType': 0, 'retTag': 0, 'tagSource': 0, 'userDefinedTag': None, 'newProvinceId': 0, 'newCityId': 0, 'newCountyId': 0, 'newTownId': 0, 'newProvinceName': None, 'used': False, 'address': None, 'name': 'xx', 'message': None, 'id': 0}, 'msgUuid': None, 'message': 'xxxxxx商品无货'}
        # 下单成功
        # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': True, 'resultCode': 0, 'orderId': 8740xxxxx, 'submitSkuNum': 1, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': None}

        if resp_json.get("success"):
            logger.info("订单提交成功! 订单号：%s", resp_json.get("orderId"))
            return True
        else:
            message, result_code = resp_json.get("message"), resp_json.get("resultCode")
            if result_code == 0:
                # self._save_invoice()
                message = message + "(下单商品可能为第三方商品，将切换为普通发票进行尝试)"
            elif result_code == 60077:
                message = message + "(可能是购物车为空 或 未勾选购物车中商品)"
            elif result_code == 60123:
                message = message + "(需要在payment_pwd参数配置支付密码)"
            logger.info("订单提交失败, 错误码：%s, 返回信息：%s", result_code, message)
            logger.info(resp_json)
            return False
    except Exception as e:
        logger.error(e)
        return False


"""
购买环节
测试三次
"""


async def buy_object(sku_id):
    for count in range(1, 2):
        logger.info("第[%s/%s]次尝试提交订单", count, 3)
        # await cancel_select_all_cart_item()
        cart = await cart_detail()
        if sku_id in cart:
            logger.info("%s 已在购物车中，调整数量为 %s", sku_id, 1)
            cart_item = cart.get(sku_id)
            await change_item_num_in_cart(
                sku_id=sku_id,
                vender_id=cart_item.get("vender_id"),
                num=1,
                p_type=cart_item.get("p_type"),
                target_id=cart_item.get("target_id"),
                promo_id=cart_item.get("promo_id"),
            )
        else:
            await add_item_to_cart(sku_id)
        risk_control = await get_checkout_page_detail()
        if risk_control == "刷新太频繁了":
            return False
        logger.info('risk_control=[%s]', risk_control)
        # if len(risk_control) > 0:
        #     if await submit_order(risk_control):
        #         return True
        logger.info("休息%ss", 3)
        await asyncio.sleep(3)
    else:
        logger.info("执行结束，提交订单失败！")
        return False


"""
查询库存
"""

"""
update by rlacat
解决skuid长度过长（超过99个）导致无法查询问题
"""


async def check_stock():
    """判断商品"""
    st_tmp = []
    len_arg = 70
    # print("skustr:",skuidStr)
    # print("skuids:",len(skuids))
    skuid_nums = len(skuids)
    skuid_batchs = math.ceil(skuid_nums / len_arg)
    # print("skuid_batchs:",skuid_batchs)
    if skuid_batchs > 1:
        if not pure_mode:
            logger.info("###数据过大 分[" + str(skuid_batchs) + "]批进行####")
        for i in range(0, skuid_batchs):
            if not pure_mode:
                logger.info("###正在处理 第[" + str(i + 1) + "]批####")
            if len_arg * (i + 1) <= len(skuids):
                # print("取个数：",len_arg*i,"至",len_arg*(i+1))
                skuidStr = ",".join(skuids[len_arg * i : len_arg * (i + 1)])
                st_tmp += await check_stock_tmp(
                    skuidStr, skuids[len_arg * i : len_arg * (i + 1)]
                )
            else:
                # print("取个数：",len_arg*i,"至",len_arg*(i+1))
                skuidStr = ",".join(skuids[len_arg * i : skuid_nums])  # skuid配置的最后一段
                # print(skuidStr)
                st_tmp += await check_stock_tmp(
                    skuidStr, skuids[len_arg * i : skuid_nums]
                )
    else:
        # <=1的情况
        skuidStr = ",".join(skuids)
        st_tmp = await check_stock_tmp(skuidStr, skuids)
    return st_tmp


async def check_stock_tmp(skuidString: str, skuids_a: List[str]):
    callback = "jQuery" + str(random.randint(1000000, 9999999))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
    }
    url = "https://c0.3.cn/stocks"
    payload = {
        "type": "getstocks",
        "skuIds": skuidString,
        "area": area,
        "callback": callback,
        "_": int(time.time() * 1000),
    }
    async with await get_session().get(url=url, params=payload, headers=headers) as resp:
        resptext = (await resp.text()).replace(callback + "(", "").replace(")", "")
    respjson = json.loads(resptext)
    inStockSkuid = []
    nohasSkuid = []
    for i in skuids_a:
        if respjson[i]["StockStateName"] != "无货":
            inStockSkuid.append(i)
        else:
            nohasSkuid.append(i)
    # print(nohasSkuid)
    if not pure_mode:
        logger.info("[%s]类型口罩无货", ",".join(nohasSkuid))
    return inStockSkuid


class JDSpider:
    """
    登陆模块作者 zstu-lly
    参考 https://github.com/zstu-lly/JD_Robot
    """

    def __init__(self):

        # init url related
        self.home = "https://passport.jd.com/new/login.aspx"
        self.login = "https://passport.jd.com/uc/loginService"
        self.imag = "https://authcode.jd.com/verify/image"
        self.auth = "https://passport.jd.com/uc/showAuthCode"

        self.sess = requests.Session()

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
            "ContentType": "text/html; charset=utf-8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
        }

        self.cookies: Dict[str, http.cookies.Morsel] = {}

        self.eid = eid
        self.fp = fp

    async def check_login(self):
        # 恢复之前保存的cookie
        checkUrl = "https://passport.jd.com/uc/qrCodeTicketValidation"
        try:
            logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            logger.info(f"检查登录状态中... ")
            with open("cookie", "rb") as f:
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
                async with get_session().get(checkUrl, cookies=cookies) as response:
                    if response.status != requests.codes.OK:
                        logger.info("登录过期, 请重新登录!")
                        return False
                    else:
                        logger.info("登陆状态正常")
                        self.cookies.update(dict(cookies))
                        return True

        except Exception as e:
            logger.error(e)
            return False

    async def login_by_QR(self):
        # jd login by QR code
        global g_cookie
        try:
            logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            logger.info(f"{time.ctime()} > 请打开京东手机客户端，准备扫码登录:")
            sess = get_session()
            urls = (
                "https://passport.jd.com/new/login.aspx",
                "https://qr.m.jd.com/show",
                "https://qr.m.jd.com/check",
                "https://passport.jd.com/uc/qrCodeTicketValidation",
            )
            # step 1: open login page
            response = await sess.get(urls[0], headers=self.headers)
            if response.status != requests.codes.OK:
                logger.error(f"获取登录页失败:{response.status}")
                return False
            # update cookies
            self.cookies.update(response.cookies)
            logger.info(self.cookies)
            logger.info(response.cookies)

            # step 2: get QR image
            response = await sess.get(
                urls[1],
                headers=self.headers,
                cookies=self.cookies,
                params={
                    "appid": 133,
                    "size": 147,
                    "t": int(time.time() * 1000),
                },
            )
            if response.status != requests.codes.OK:
                logger.error(f"获取二维码失败:{response.status}")
                return False

            # update cookies
            self.cookies.update(response.cookies)

            # save QR code
            image_file = "qr.png"
            with open(image_file, "wb") as f:
                f.write(await response.read())

            # scan QR code with phone
            if os.name == "nt":
                # for windows
                import matplotlib.pyplot as plt
                import matplotlib.image as mpimg
                img = mpimg.imread(image_file)
                plt.imshow(img)
                plt.axis('off')
                plt.show()
                # os.system("start " + image_file)
            else:
                if os.uname()[0] == "Linux":
                    # for linux platform
                    os.system("eog " + image_file)
                else:
                    # for Mac platform
                    os.system("open " + image_file)

            # step 3: check scan result    京东上也是不断去发送check请求来判断是否扫码的
            self.headers["Host"] = "qr.m.jd.com"
            self.headers["Referer"] = "https://passport.jd.com/new/login.aspx"

            # check if QR code scanned
            qr_ticket = None
            retry_times = 100  # 尝试100次
            logger.info(self.cookies)
            while retry_times:
                retry_times -= 1
                async with sess.get(
                    urls[2],
                    headers=self.headers,
                    cookies=self.cookies,
                    params={
                        "callback": "jQuery%d" % random.randint(1000000, 9999999),
                        "appid": 133,
                        "token": self.cookies["wlfstk_smdl"].value,
                        "_": int(time.time() * 1000),
                    },
                ) as response:
                    if response.status != requests.codes.OK:
                        continue
                    text = await response.text()
                    logger.info(text)
                    rs = json.loads(re.search(r"{.*?}", text, re.S).group())
                    if rs["code"] == 200:
                        logger.info(f"{rs['code']} : {rs['ticket']}")
                        qr_ticket = rs["ticket"]
                        break
                    else:
                        logger.info(f"{rs['code']} : {rs['msg']}")
                        await asyncio.sleep(3)

            if not qr_ticket:
                logger.error("二维码登录失败")
                return False

            # step 4: validate scan result
            # must have
            self.headers["Host"] = "passport.jd.com"
            self.headers["Referer"] = "https://passport.jd.com/new/login.aspx"
            async with sess.get(
                urls[3],
                headers=self.headers,
                cookies=self.cookies,
                params={"t": qr_ticket},
            ) as response:
                if response.status != requests.codes.OK:
                    logger.error(f"二维码登录校验失败:{response.status}")
                    return False
                raw_text = await response.read()

            # 京东有时候会认为当前登录有危险，需要手动验证
            # url: https://safe.jd.com/dangerousVerify/index.action?username=...
            res = orjson.loads(raw_text)
            if not response.headers.get("p3p"):
                if "url" in res:
                    logger.info(f"需要手动安全验证: {res['url']}")
                    return False
                else:
                    logger.info(res)
                    logger.info("登录失败!!")
                    return False

            # login succeed
            self.headers["P3P"] = response.headers.get("P3P")
            self.cookies.update(response.cookies)
            g_cookie = response.cookies
            # 保存cookie
            with open("cookie", "wb") as f:
                pickle.dump(self.cookies, f)
            return True

        except Exception as e:
            logger.error(e)
            raise


spider = JDSpider()

"""
检测商品是否下柜，增加多线程方式
"""


class item_process(threading.Thread):
    def __init__(self, threadID, name, skuid):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.skuid = skuid

    def run(self):
        # print ("开始线程["+self.skuid+"]：" + self.name)
        is_item_removed(self.skuid)
        # print ("退出线程:"+ self.name)


async def auto_buy(in_stock_sku_id):
    # 参数：有货的商品列表
    threads = []
    i = 1
    for sku_id in in_stock_sku_id:
        # print(skuId)
        t = item_process(
            i, "item_exist_" + str(sku_id), sku_id
        )  # 循环 实例化i个Thread类，传递函数及其参数，并将线程对象放入一个列表中
        threads.append(t)
        threads[i - 1].start()  # 循环 开始线程
        if threading.activeCount() > thread_max_nums:  # 限制最多进程个数
            if not pure_mode:
                logger.info("###[等待]已到达配置最大进程数[" + str(thread_max_nums) + "]###")
            for j in range(i):
                threads[j].join()  # 循环 join()方法可以让主线程等待所有的线程都执行完毕。
                j += 1
        i += 1


async def clean_and_buy(sku_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        "Host": "item.jd.com",
    }
    url = "https://item.jd.com/{}.html".format(sku_id)
    async with get_session().get(url=url, headers=headers, cookies=g_cookie) as resp:
        # return '该商品已下柜' not in page.text
        page = await resp.text()
        if "该商品已下柜" not in page:
            logger.info("[%s]类型口罩有货啦!马上下单", sku_id)
            skuidUrl = "https://item.jd.com/" + sku_id + ".html"
            if await buy_object(sku_id):
                # sendMail(mail, skuidUrl, True)
                await message.send(skuidUrl, True)
                return
            else:
                # sendMail(mail, skuidUrl, False)
                await message.send(skuidUrl, False)
        else:
            if not pure_mode:
                logger.info("[%s]类型口罩有货，但已下柜商品", sku_id)




async def main():
    flag = 1
    while 1:
        try:
            if flag == 1:
                await validate_cookies()
                await getUsername()
            checkSession = requests.Session()
            checkSession.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                "Connection": "keep-alive",
            }
            starttime = datetime.datetime.now()
            flag += 1
            inStockSkuid = await check_stock()
            await auto_buy(inStockSkuid)
            await asyncio.sleep(timesleep)
            if flag % 20 == 0:
                logger.info("校验是否还在登录")
                await validate_cookies()
            endtime = datetime.datetime.now()
            logger.info(
                "第"
                + str(flag)
                + "次检测结束.耗时： "
                + str((endtime - starttime).seconds)
                + "s"
            )
        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
