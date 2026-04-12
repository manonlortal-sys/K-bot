import discord
from config import ORG_ROLE_ID, PARTICIPANT_ROLE_ID

def is_organizer(member: discord.Member) -> bool:
    return any(role.id == ORG_ROLE_ID for role in member.roles)

def is_participant(member: discord.Member) -> bool:
    return any(role.id == PARTICIPANT_ROLE_ID for role in member.roles)