from constants import MEDALS, HEROES_DICT
from datetime import datetime
from zoneinfo import ZoneInfo

msk_tz = ZoneInfo("Europe/Moscow")

def format_rank(season_rank: int):
    if not season_rank:
        return "У вас нет ранга"
    medal = season_rank // 10
    stars = season_rank % 10
    
    medal_name = MEDALS.get(medal)
    return f"{medal_name} {stars}★"

def format_heroes(data: dict):
    unsorted_heroes = []
    heroes_data = data['heroesGroupBy']
    for hero in heroes_data:
        unsorted_heroes.append({
            "id" : hero['heroId'],
            "matchCount" : hero['matchCount'],
            "winCount" : hero['winCount'],
            "avgKills" : hero['avgKills'],
            "avgDeaths" : hero['avgDeaths'],
            "avgAssists" : hero['avgAssists'],
            "GPM" : hero['avgGoldPerMinute'],
            "EPM" : hero['avgExperiencePerMinute'],
            "lastMatchDateTime" : hero['lastMatchDateTime']
        })
    sorted_heroes = sorted(unsorted_heroes, key=lambda x: x['lastMatchDateTime'], reverse=True)
    return sorted_heroes[:5]

def format_matches(data: dict):
    matches = []
    matches_data = data['matches']
    for match in matches_data:
        player = match['players'][0]
        id = match['id']
        hero = player['hero']['displayName']
        duration_sec = match['durationSeconds']
        duration_min = duration_sec // 60
        seconds = duration_sec % 60
        kills = player['kills']
        deaths = player['deaths']
        assists = player['assists']
        matches.append({
            "id" : id,
            "hero" : hero,
            "duration_min" : duration_min,
            "seconds" : seconds,
            "kills" : kills,
            "deaths" : deaths,
            "assists" : assists
        })
    return matches

def format_player(data: dict, topic: str):
    if topic == "matches":
        n = 0
        matches_list = format_matches(data)
        formatted_matches = []
        for m in matches_list:
            n += 1
            line = (
                f"{n}. "
                f"<b>id матча: {m['id']}</b>\n"
                f"Герой: {m['hero']}\n"
                f"Длительность матча: {m['duration_min']}:{m['seconds']:02d}\n"
                f"KDA: {m['kills']}/{m['deaths']}/{m['assists']}\n"
                f"--------------------------"
            )
            formatted_matches.append(line)
        return "\n".join(formatted_matches)
    if topic == "rank":
        season_rank = data['ranks'][0]['rank']
        rank = format_rank(season_rank=season_rank)
        return f"Ваш ранг: {rank}"
    if topic == 'winrate':
        match_count = data['matchCount']
        wins = data['winCount']
        return f"Винрейт: {wins/match_count*100:.1f}%\n Всего игр:{match_count}\n Выиграно игр: {wins}"
    if topic == "heroes":
        heroes_list = format_heroes(data)
        formatted_heroes = []
        for h in heroes_list:
            time = h['lastMatchDateTime']
            date_msk = datetime.fromtimestamp(time, tz=msk_tz)
            line = (
                f"Герой: {HEROES_DICT.get(h['id'])}\n"
                f"Всего матчей: {h['matchCount']}\n"
                f"Выиграно матчей: {h['winCount']}\n"
                f"Средние показатели на герое: {h['avgKills']:.0f}/{h['avgDeaths']:.0f}/{h['avgAssists']:.0f}\n"
                f"Среднее количество золота в минуту: {h['GPM']}\n"
                f"Среднее количество опыта в минуту: {h['EPM']}\n"
                f"Последняя игра на герое: {date_msk.strftime('%Y-%m-%d %H:%M:%S МСК')}\n"
                f"---------------------------------------------------"
            )
            formatted_heroes.append(line)
        return "\n".join(formatted_heroes)
    
    return