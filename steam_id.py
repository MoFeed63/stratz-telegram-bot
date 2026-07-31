import httpx
from bs4 import BeautifulSoup
from constants import STEAM_ID64_BASE

async def get_steam_id(text):
    if "https://" in text:
        url_id = text + "?xml=1"
    else:
        url_id = f"https://steamcommunity.com/id/{text}/?xml=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url_id)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml-xml")
        steam_id = int(soup.find('steamID64').text)
    return steam_id - STEAM_ID64_BASE

