def is_already_captain(user_id, teams):
    return any(team["captain_id"] == user_id for team in teams)
