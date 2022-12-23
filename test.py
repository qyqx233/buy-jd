import asyncio
import pickle
import requests

from jd_automask_V1 import (
    clean_and_buy,
    JDSpider,
    restore_cookie,
    cancel_select_all_cart_item,
    cart_detail,
)
from util.http import init_session, close_sessoin, get_session
import ssl
from aiohttp.cookiejar import CookieJar

ssl._create_default_https_context = ssl._create_unverified_context


async def test_http():
    async with Context():
        resp = await get_session().get("https://baidu.com", verify_ssl=False)
        print(await resp.content())


async def test_login():
    async with Context():
        jd = JDSpider()
        await jd.login_by_QR()


async def test_login_cookie():
    async with Context():
        jd = JDSpider()
        await jd.check_login()


async def test_check_sku():
    async with Context():
        await clean_and_buy("10064945329734")


class Context:
    async def __aenter__(self, *args):
        await init_session()
        restore_cookie()

    async def __aexit__(self, *args):
        await close_sessoin()


async def test_cancel():
    async with Context():
        await cancel_select_all_cart_item()


async def test_cart_detail():
    async with Context():
        jd = JDSpider()
        # await jd.login_by_QR()
        await cart_detail()

async def test_cookie():
    ck = CookieJar()
    with open('cookie', 'rb') as f:
        cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
    ck.update_cookies(cookies)
    req_cookies = ck.filter_cookies('https://cart.jd.com/card_index')
    print(dict(req_cookies))

async def test_requests_cart():
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        # "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.46",
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36 Edg/108.0.1462.46',
        # 'cookie': '__jdu=1661910668612278975324; shshshfpa=653e755b-078e-39ad-2f56-87cb4f7e1452-1663035165; shshshfpb=zON7kDZ8iOcPqN4FHqiVEfQ; pinId=jqZ52RBYPAg; unpl=JF8EAKpnNSttW0pVUhwBHBNHG1gEW1lYGB4LaWRQAQgNGFUMGgYZFRF7XlVdXhRLFB9ubxRUW1NIVQ4ZCisSEXtfVVdcDkgWA25XNVNdUQYVV1YyGBIgS1xkXloPSx8DbmACXVpYSFcDEgodFhJIWGRfbQ9LHjNfVwBUXFlPVwMdARMiEXtfVV9YAEkfAGZmNR8zWQZUAhwCExIRTFpdWV0LSBEKZ2EBVl5de1U1GA; __jdv=122270672|t.zoukankan.com|t_308072010_|tuiguang|200f6260fa4a45ab8972ddddb0805360|1670577639787; areaId=12; PCSYCityID=CN_320000_320500_0; TrackID=1Y_yhqBtqD6JK1NzPThMgVKnl0CnR3XVMUKbNxh7IwKHqcu8k4ZHF-SHYs2H4EnCVp64-fqmwDrCpdLG_0HmcNm0U_JNqT7Jt5qeKE9byqUB4u_YFHzLUR9b_kKkcfwYV; pin=ZHCQXCN; unick=jd_ZHCQ689; ceshi3.com=201; _tp=agSrkpFZW11Yv31WgbVM5Q%3D%3D; _pst=ZHCQXCN; user-key=fefa3982-d781-470d-8e25-b63bed25a7ab; cart-main=xx; ipLoc-djd=12-988-993-58088; __jda=122270672.1661910668612278975324.1661910669.1671675920.1671692217.14; __jdc=122270672; shshshfp=58020db4702bdcfd37cf2401658ccce7; __jdb=122270672.9.1661910668612278975324|14.1671692217; shshshsID=e356cf4b3dc9df06516c26a878251530_9_1671693384632; cn=1; 3AB9D23F7A4B3C9B=2MSCNAZALJDJJMKC5BL5HRSJ5LAU3PRBDLWKVYU4HWKQHBSXCLYM25VPPJL4PETFSTCHY3ZIUJ2GDNA2RVWAQNYVKQ; thor=721A15BBA257F57947AF0765749B339CF86E6C10D1BDCCE530EAAB673FBA1F02F6E89AD12F4CCF4712705000206CBA9E604E8DBF7B56F070FD9E3E966D1F6CE2CA006FB552490F6CBBC6D1D845CB374B608A1B69FF44C96ADEAEF23BADBB2422855F3DCAE636CAEE6F449A9F902899A5BA83E2A0A8732ED3F8C9D1A7F6460ADF2A2C04DC48615583354361785FA28214',
        'cookie': '__jdu=1661910668612278975324; shshshfpa=653e755b-078e-39ad-2f56-87cb4f7e1452-1663035165; shshshfpb=zON7kDZ8iOcPqN4FHqiVEfQ; pinId=jqZ52RBYPAg; unpl=JF8EAKpnNSttW0pVUhwBHBNHG1gEW1lYGB4LaWRQAQgNGFUMGgYZFRF7XlVdXhRLFB9ubxRUW1NIVQ4ZCisSEXtfVVdcDkgWA25XNVNdUQYVV1YyGBIgS1xkXloPSx8DbmACXVpYSFcDEgodFhJIWGRfbQ9LHjNfVwBUXFlPVwMdARMiEXtfVV9YAEkfAGZmNR8zWQZUAhwCExIRTFpdWV0LSBEKZ2EBVl5de1U1GA; __jdv=122270672|t.zoukankan.com|t_308072010_|tuiguang|200f6260fa4a45ab8972ddddb0805360|1670577639787; areaId=12; PCSYCityID=CN_320000_320500_0; TrackID=1Y_yhqBtqD6JK1NzPThMgVKnl0CnR3XVMUKbNxh7IwKHqcu8k4ZHF-SHYs2H4EnCVp64-fqmwDrCpdLG_0HmcNm0U_JNqT7Jt5qeKE9byqUB4u_YFHzLUR9b_kKkcfwYV; pin=ZHCQXCN; unick=jd_ZHCQ689; ceshi3.com=201; _tp=agSrkpFZW11Yv31WgbVM5Q%3D%3D; _pst=ZHCQXCN; user-key=fefa3982-d781-470d-8e25-b63bed25a7ab; ipLoc-djd=12-988-993-58088; cn=1; __jda=76161171.1661910668612278975324.1661910669.1671692217.1671699528.15; __jdc=76161171; thor=721A15BBA257F57947AF0765749B339CF86E6C10D1BDCCE530EAAB673FBA1F02060212B1C5FF6456BBFD3DC352AD68AC298450203525E79E19CDE1239284B56E8CFF7753566BD100AF04E42BD80559C2A6B1162DD5BC1F9AC45E12EA4BF98885C82A62907AAF2FC99EA63789462BDF8B158AFD84BEB987636759BD7B028C9DBD901AEFDB2B0E054BB0359C66EAAA4E87; wxa_level=1; retina=1; cid=9; jxsid=16716995696833619761; appCode=ms0ca95114; webp=1; mba_muid=1661910668612278975324; visitkey=4368053983656068; PPRD_P=UUID.1661910668612278975324; sc_width=576; _gia_s_local_fingerprint=ba95aa2e924aa42cbbb52ce3aec7b23d; equipmentId=2MSCNAZALJDJJMKC5BL5HRSJ5LAU3PRBDLWKVYU4HWKQHBSXCLYM25VPPJL4PETFSTCHY3ZIUJ2GDNA2RVWAQNYVKQ; fingerprint=ba95aa2e924aa42cbbb52ce3aec7b23d; deviceVersion=108.0.0.0; deviceOS=android; deviceOSVersion=6.0; deviceName=Chrome; _gia_s_e_joint={"eid":"2MSCNAZALJDJJMKC5BL5HRSJ5LAU3PRBDLWKVYU4HWKQHBSXCLYM25VPPJL4PETFSTCHY3ZIUJ2GDNA2RVWAQNYVKQ","ma":"","im":"","os":"Android 6.x","ip":"114.218.50.15","ia":"","uu":"","at":"6"}; jcap_dvzw_fp=g2_JrRGuzrKKP5kWeS0yiSQXmNsRb_-fyPeDDkD_LAsWKXp4XTs17HSyYd1isrgvkZJDOw==; whwswswws=; 3AB9D23F7A4B3C9B=2MSCNAZALJDJJMKC5BL5HRSJ5LAU3PRBDLWKVYU4HWKQHBSXCLYM25VPPJL4PETFSTCHY3ZIUJ2GDNA2RVWAQNYVKQ; TrackerID=aR-0XjVJFkzpL1WDQo1eYRVQXDbBC48RswoW6fYE9PBo43so4ZjMrxwXewmST88SZ2Y1-GfaypJDxyysJbx7VxfvFzjDWrMOeeZGB9-Ak7BBUN2YLSNChw21cNl8Y6Dc; pt_key=AAJjpBzmADASqvJLytykzB2e10rDc1HKuIKtvTQ6VXoTq9GePEK3OfErwdsDovZqq5jCi07YPz4; pt_pin=ZHCQXCN; pt_token=s7c8bncs; pwdt_id=ZHCQXCN; sfstoken=tk01mce471d0ca8sM3gxSm9QbmlWybk4gaTFK+6UBxLffrRlLrTn2mAmdOxLM2pFZUIOlCcV6Sl7ltcv8huLDPgOYiUi; shshshfp=f1d70ef11295ce9878390d33e97c43b3; __wga=1671699701694.1671699606274.1671699606274.1671699606274.4.1; jxsid_s_t=1671699701731; jxsid_s_u=https%3A//home.m.jd.com/myJd/newhome.action; shshshsID=bfece5df3401cd4aa60d4582158ff273_7_1671699701838; wqmnx1=MDEyNjM2MnRtb2U9aTE5MTU1NW8vTCBpO3NpQUFlNSBMZW9vODBsYTdkLjI5c2RhMjJPRCkmSA%3D%3D; __jdb=76161171.12.1661910668612278975324|15.1671699528; mba_sid=16716995698115509338255070730.11; autoOpenApp_downCloseDate_jd_homePage=1671699708535_1; __jd_ref_cls=MCommonBottom_Cart',
    }
    res = requests.get('https://p.m.jd.com/cart/cart.action?fromnav=1', headers=headers)
    with open('cart_requests_mobile.html', 'wb') as fd:
        fd.write(res.content)

if __name__ == "__main__":
    # asyncio.run(test_check_sku())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_requests_cart())
