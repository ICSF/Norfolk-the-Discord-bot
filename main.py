import discord
import secrets
import sqlite3

from nodules import modmessage, treasure, picocoin, games, fish


client = discord.Client()


@client.event
async def on_ready():
    client.dbconn = sqlite3.connect('main.db')
    client.dbconn.row_factory = sqlite3.Row
    client.nodules = [x.Nodule(client) for x in (modmessage, treasure, picocoin, games, fish)]
    client.picoguild = client.get_guild(807940337020567589)

    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name='such pico, much con'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!nping'):
        await message.channel.send('npong!')

    for nodule in client.nodules:
        await nodule.on_message(message)


@client.event
async def on_raw_reaction_add(payload):
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