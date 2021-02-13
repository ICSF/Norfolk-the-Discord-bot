import discord
import secrets


client = discord.Client()


@client.event
async def on_ready():
    global icsf
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name='such pico, much con'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return


@client.event
async def on_raw_reaction_add(payload):
    pass

client.run(secrets.token)
