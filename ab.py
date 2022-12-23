import bs4

soup = bs4.BeautifulSoup(b'<html></html>', 'html.parser')
print(soup)