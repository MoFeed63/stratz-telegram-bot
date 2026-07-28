import os
from dotenv import load_dotenv
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright
import json
import asyncio
# from steam_id import get_steam_id

load_dotenv()
api_token = os.getenv("API_TOKEN")


QUERY = """
query GetPlayerHeroesStats($steamId: Long!, $heroesGroupByRequest: PlayerMatchesGroupByRequestType!) {
  player(steamAccountId: $steamId) {
    steamAccountId
    matchCount
    winCount
    behaviorScore
    steamAccount {
      id
      name           # personaname
      avatar
      seasonRank
      seasonLeaderboardRank
      profileUri
    }
    ranks {
      rank
      seasonRankId
      isCore
      asOfDateTime
    }
    matches(request: {take: 5}) {
      id
      startDateTime
      durationSeconds
      didRadiantWin
      players(steamAccountId: $steamId) {
        heroId
        hero { displayName }
        kills
        deaths
        assists
        networth
        goldPerMinute
        experiencePerMinute
        isVictory
        isRadiant
        item0Id
        item1Id
        item2Id
        item3Id
        item4Id
        item5Id
        backpack0Id
        backpack1Id
        backpack2Id
      }
    }
    heroesGroupBy: matchesGroupBy(request: $heroesGroupByRequest) {
      ... on MatchGroupByHeroType {
        heroId
        matchCount
        winCount
        avgGoldPerMinute
        avgExperiencePerMinute
        lastMatchDateTime
        avgAssists
        avgKills
        avgDeaths
      }
    }
  }
}
"""



headers={
    "Authorization": f"Bearer {api_token}",
}


async def get_player(account_id: int) -> dict:
    variables = {
        "steamId": account_id,
        "heroesGroupByRequest": {
            "groupBy": "HERO",
            "playerList": "SINGLE",
            "skip": 0,
            "take": 1000
        }
    }
    async with AsyncSession(impersonate="chrome") as session:
        resp = await session.post(
            "https://api.stratz.com/graphql",
            json={"query": QUERY, "variables": variables},
            headers=headers,
            timeout=30.0
        )
        resp.raise_for_status()
        if resp.status_code != 200:
            return {"error": "Блокировка", "status": resp.status_code}
        data = resp.json()
        print(data)
        return data['data']['player']

# asyncio.run(get_player(1172601372))