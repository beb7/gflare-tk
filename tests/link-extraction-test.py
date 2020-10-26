from lxml.html import fromstring
import requests

url = 'http://www.valedoo.com'

response = requests.get(url)

def get_links(content):
    tree = fromstring(content)
    links = []
    xpath = "//a/@href | //link[@rel='canonical'] | //link[@rel='alternate']/@href | //link[@rel='canonical']/@href | //link[@rel='next']/@href | //link[@rel='prev']/@href"
    try:
        for link in tree.xpath('//script/@src'):
            links.append(link)
    except Exception as e:
        print(e)
        return []
    return list(set(links))


links = get_links(response.content)

print(links)
