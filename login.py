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

bot = commands.Bot(command_prefix='/', intents=intents) # The bot, subclass of Client


# Some constants
RULES_ACKNOWLEDGE_EMOJI = '✅' # ":white_check_mark:"
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

    """
    with open(filename, 'r') as file:
        for line in file:
            line = line.split()
            key = line[0]
            value = line[1]
            variable_dict[key] = value


# Dictionary of rules messages per guild
rules_messages = dict()
read_config_file(RULES_MESSAGE_FILE, rules_messages)

# Dictionary of roles messages per guild
roles_messages = dict()
read_config_file(ROLES_MESSAGE_FILE, roles_messages)


##################
### Bot Events ###
##################

# Basic logging on login
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

    # List all the guilds this bot is a member of
    print("Visible guilds:")
    for guild in bot.guilds:
        print(f"\t {guild.name} (ID:{guild.id})")


@bot.event
async def on_member_join(member: discord.Member):
    # Welcome the member to the server
    WELCOME_MESSAGE = f"Hello {member.mention} and welcome to " + \
    f"{member.guild.name}!\nRemember to read the rules before engaging" + \
    f"with the server."

    await member.guild.system_channel.send(content=WELCOME_MESSAGE)



@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):

    print(f"Caught reaction {repr(payload.emoji)} on message {repr(payload.message_id)}")

    # Determine if this was a reaction on the rules message or the role message
    guild_id = payload.guild_id
    rules_message = rules_messages[guild_id]
    roles_message = roles_messages[guild_id]

    if payload.message_id == rules_message:
        if payload.event_type != "REACTION_ADD" or payload.emoji.name != RULES_ACKNOWLEDGE_EMOJI:
            return
        
        member = payload.member
        await member.add_roles(member.guild.roles[1])

    elif payload.message_id == roles_message:
        if payload.event_type != "REACTION_ADD":
            return
        
        member = payload.member
        reaction = payload.emoji
        
        # TODO: Need mapping from emojis to roles


####################
### Bot Commands ###
####################

@bot.command()
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

    rules_messages[guild_id] = message_id
    with open(RULES_MESSAGE_FILE, 'a') as file:
        file.write(f"{guild_id} {message_id}")


@bot.command()
async def del_rules(context: commands.Context):
    guild_id = context.guild.id

    del rules_messages[guild_id]
    with open(RULES_MESSAGE_FILE, 'r') as file:
        lines = file.readlines()
    with open(RULES_MESSAGE_FILE, 'w') as file:
        for line in lines:
            data = line.split()
            if data[0] == guild_id:
                continue
            else:
                file.write(line)


@bot.command()
async def get_rules(context: commands.Context):
    args = context.message.content.split()
    guild_id = context.guild.id
    context.channel(rules_messages[guild_id])


# Code stops here

bot.run(TOKEN)
