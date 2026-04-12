import re

def parse_players(content: str):
    mentions = re.findall(r"<@!?(\d+)>", content)

    cleaned = re.sub(r"<@!?(\d+)>", "", content)
    raw = cleaned.split()

    players = list(set(mentions + raw))

    return players[:2]