from config import ORG_ROLE_ID

def is_organizer(member):
    return any(role.id == ORG_ROLE_ID for role in member.roles)