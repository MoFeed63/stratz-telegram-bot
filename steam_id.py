import httpx
from bs4 import BeautifulSoup

async def get_steam_id(url):
    url_id = url + "?xml=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url_id)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml-xml")
        steam_id = int(soup.find('steamID64').text)
    return steam_id

