"""
login.py

Main file for the Neodymium Discord automod bot.
Note: The "rules message" is an arbitrary message sent in a guild that new
members must acknowledge to be granted the base role. A guild can have no rules
message, or a message can be specified using get_rules().

Author: Kent Carrier | @embite | kentbo0528@gmail.com

"""


import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

load_dotenv()                       # Load the .env file
TOKEN = os.getenv("DISCORD_TOKEN")  # Load login token from .env

# Intents, whatever those are
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

# Instantiate the bot, subclass of Client
bot = commands.Bot(command_prefix='/', intents=intents)

# Contains per-guild config info
class GuildContext:
    id: int
    RulesMessageID: int
    RolesMessageID: int
    Emoji_Role_Map: dict

    def __init__(self, id, RulesMessageID=0, RolesMessageID=0, Emoji_Role_Map=dict()):
        self.id = id
        self.RulesMessageID = RulesMessageID
        self.RolesMessageID = RolesMessageID
        self.Emoji_Role_Map = Emoji_Role_Map
    
    def __repr__(self):
        return f"GuildContext(id={self.id}, RulesMessageID={self.RulesMessageID}, " + \
             f"RolesMessageID={self.RolesMessageID}, Emoji_Role_Map={repr(self.Emoji_Role_Map)})"
    
    def __setattr__(self, name: str, value: os.Any):
        if name == "id":
            raise AttributeError("Cannot modify id of a GuildContext")
        else:
            return type.__setattr__(self, name, value)

    def __eq__(self, other: 'GuildContext'):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


# Some constants

# The emoji that members need to react to the rules message with in order to be
# granted a role
RULES_ACKNOWLEDGE_EMOJI = '✅' # ":white_check_mark:"

# Config file names
RULES_MESSAGE_FILE = "rules.txt"
ROLES_MESSAGE_FILE = "roles.txt"

#############################
### Config/initialization ###
#############################

def read_config_file(filename, variable_dict: dict):
    """
    Read in a config file with lines formatted like:

        key1 value1
        key2 value2
        key3 value3

    Ill-formatted lines may or may not be ignored.

    NOTE: Only adds or replaces entries to the dictionary. No elements are
    removed if already present (unless overwritten).
    """
    with open(filename, 'r') as file:
        for line in file:
            line = line.split()
            if len(line) < 2:
                continue
            key = line[0]
            value = line[1]
            variable_dict[key] = value


# Dictionary mapping guild ids to GuildContext structs
# Instantiate here, initialize in on_ready()
guilds_ctx = dict[int, GuildContext]


##################
### Bot Events ###
##################

# Basic logging on login
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

    # List all the guilds this bot is a member of
    # Build the dictionary of guild contexts
    print("Visible guilds:")
    for guild in bot.guilds:
        print(f"\t {guild.name} (ID:{guild.id})")
        guilds_ctx[guild.id] = GuildContext(guild.id)



@bot.event
async def on_guild_join(guild: discord.Guild):
    """
    Updated the guilds_ctx dictionary after joining a new guild.
    """
    print(f"Joined Guild: {guild.name} (ID:{guild.id})")
    guilds_ctx[guild.id] = GuildContext(guild.id)



@bot.event
async def on_member_join(member: discord.Member):
    # Welcome the member to the server
    WELCOME_MESSAGE = f"Hello {member.mention} and welcome to " + \
    f"{member.guild.name}!\nRemember to read the rules before engaging" + \
    f"with the server."

    await member.guild.system_channel.send(content=WELCOME_MESSAGE)



@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):

    # Don't do anything when the bot changes reactions
    if payload.member == bot:
        return

    # Only do something if a reaction is added
    if payload.event_type != "REACTION_ADD":
        return

    print(f"Caught reaction {repr(payload.emoji)} on message {repr(payload.message_id)}")

    # Determine if this was a reaction on the rules message or the role message
    guild = payload.member.guild
    guild_ctx: GuildContext = guilds_ctx[guild.id]

    if payload.message_id == guild_ctx.RulesMessageID:
        # Rules were acknowledged by a member; give member the base role

        if payload.emoji.name != RULES_ACKNOWLEDGE_EMOJI:
            return
        
        member = payload.member
        await member.add_roles(guild.roles[1])

    elif payload.message_id == guild_ctx.RolesMessageID:
        # A role was requested by the member
        
        member   = payload.member
        reaction = payload.emoji.id
        role     = guild_ctx.Emoji_Role_Map[reaction].id

        # Grant or remove the role
        if role != None:
            if member.get_role(role) == None:
                member.add_roles(role)
            else:
                member.remove_roles(role)
        
        # Remove the reaction from the message
        guild.get_channel(payload.channel_id) \
            .get_partial_message(payload.message_id) \
            .remove_reaction(payload.emoji)


####################
### Bot Commands ###
####################

@bot.command()
# Only allow server admins to invoke this command
@commands.has_permission(administrator=True)
async def set_rules(context: commands.Context):
    """
    Set the rules message for a particular guild.
    """
    args = context.message.content.split()
    try:
        guild_id = context.guild.id
        message_id = args[1]
    except:
        await context.channel.send("Bad arguments formatting")
        return

    with open(RULES_MESSAGE_FILE, 'a') as file:
        file.write(f"{guilds_ctx[guild_id].RulesMessageID} {message_id}")


@bot.command()
# Only allow server admins to invoke this command
@commands.has_permissions(administrator=True)
async def del_rules(context: commands.Context):
    """
    Removes the current guild from the config, so the bot forgets there's a
    rules message
    """
    guild_ctx = guilds_ctx[context.guild.id]

    guild_ctx.RulesMessageID = 0
    with open(RULES_MESSAGE_FILE, 'r') as file:
        lines = file.readlines()
    with open(RULES_MESSAGE_FILE, 'w') as file:
        for line in lines:
            data = line.split()
            if data[0] == guild_ctx.id:
                continue
            else:
                file.write(line)


@bot.command()
async def get_rules(context: commands.Context):
    """
    Get the ID of the rules message
    """
    context.channel.send(guilds_ctx[context.guild.id].RulesMessageID)


### These functions are basically identical to the above, but for roles rather than rules
# TODO: Find a better way to distinguish the two with more than one letter

@bot.command()
# Only allow server admins to invoke this command
@commands.has_permission(administrator=True)
async def set_roles_msg(context: commands.Context):
    """
    Set the rules message for a particular guild.
    """
    args = context.message.content.split()
    try:
        guild_id = context.guild.id
        message_id = args[1]
    except:
        await context.channel.send("Bad arguments formatting")
        return

    with open(ROLES_MESSAGE_FILE, 'a') as file:
        file.write(f"{guilds_ctx[guild_id].RolesMessageID} {message_id}")


@bot.command
# Only allow server admins to invoke this command
@commands.has_permission(administrator=True)
async def set_role_emoji(context: commands.Context):
    """
    Set associations between emoji reactions and roles
    """
    guild = context.guild
    guild_ctx: GuildContext = guilds_ctx[guild.id]

    args = context.message.content.split()

    if len(args) < 3:
        await context.channel.send("Bad arguments formatting")
        return

    emoji_id = args[1]
    if guild.fetch_emoji(emoji_id) == None:
        await context.channel.send("Bad argument or invalid emoji ID")
        return
    
    role_id = args[2]
    if guild.fetch_roles(role_id) == None:
        await context.channel.send("Bad argument or invalid role ID")
        return

    if guild_ctx.Emoji_Role_Map.contains(emoji_id):
        return

    guild_ctx.Emoji_Role_Map[emoji_id] = role_id

    # TODO: Save associations to disk


@bot.command()
# Only allow server admins to invoke this command
@commands.has_permissions(administrator=True)
async def del_roles(context: commands.Context):
    """
    Removes the current guild from the config, so the bot forgets there's a
    roles message
    """
    guild_ctx = guilds_ctx[context.guild.id]

    guild_ctx.RolesMessageID = 0
    with open(ROLES_MESSAGE_FILE, 'r') as file:
        lines = file.readlines()
    with open(ROLES_MESSAGE_FILE, 'w') as file:
        for line in lines:
            data = line.split()
            if data[0] == guild_ctx.id:
                continue
            else:
                file.write(line)


@bot.command()
async def get_roles(context: commands.Context):
    """
    Get the ID of the roles message
    """
    context.channel.send(guilds_ctx[context.guild.id].RolesMessageID)


# Code stops here

bot.run(TOKEN)
