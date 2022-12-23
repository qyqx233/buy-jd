import pickle
import requests
from pathlib import Path
from bs4 import BeautifulSoup


def main():
    session = requests.session()
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Connection": "keep-alive",
    }

    with open("cookie", "rb") as f:
        cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
        session.cookies = dict(cookies)
    print(cookies)

    url = 'https://cart.jd.com/cart.action'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Host": "cart.jd.com",
        "Connection": "keep-alive"
    }
    resp = session.get(url, headers=headers)
    p = Path("card_detail2.html")
    p.open(mode='wb')
    p.write_text(resp.text)
    # soup = BeautifulSoup(resp.text, "html.parser")
    # print(soup)

main()