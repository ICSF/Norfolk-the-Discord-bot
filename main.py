import discord
import secrets
import sqlite3
from importlib import reload

from nodules import modmessage, treasure, picocoin, games, fish, sillyvoices, talks, cleverbot
_nodules = (modmessage, treasure, games, fish, sillyvoices, talks, cleverbot)


client = discord.Client()


@client.event
async def on_ready():
    client.dbconn = sqlite3.connect('main.db')
    client.dbconn.row_factory = sqlite3.Row
    client.picoguild = client.get_guild(807940337020567589)
    client.nodules = [picocoin.Nodule(client)]
    load()

    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name='such pico, much con'))


def load():
    client.nodules = client.nodules[:1]
    client.nodules.extend([x.Nodule(client) for x in _nodules])


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!nping'):
        await message.channel.send('npong!')

    if message.content.startswith('!reload') and (message.author.id == 133647238235815936 or message.author.guild_permissions.administrator):
        print("Reloading Nodules")
        for n in _nodules:
            reload(n)
        load()
        await message.channel.send(":recycle: Nodules reloaded")

    for nodule in client.nodules:
        await nodule.on_message(message)


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return

    for nodule in client.nodules:
        await nodule.on_raw_reaction_add(payload)

# client.run(secrets.token)
try:
    client.loop.run_until_complete(client.start(secrets.token))
except KeyboardInterrupt:
    client.loop.run_until_complete(client.logout())
    # cancel all tasks lingering
finally:
    client.dbconn.close()
    client.loop.close()
    print("Closed")