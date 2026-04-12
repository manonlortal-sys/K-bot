from core.state import tournament

def create_team(captain_id: int, players: list):
    players = list(set(players + [captain_id]))

    team = {
        "id": str(captain_id),
        "name": None,
        "captain_id": captain_id,
        "players": players
    }

    tournament["teams"].append(team)

    return team
