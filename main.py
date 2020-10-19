import discord
import secrets

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$nothing'):
        await message.channel.send("Move Along, Nothing to See Here!".upper())

# @client.event
# async def on_raw_reaction_add(reaction, user):
#     if reaction.message.channel.id == 689605126465388552:
#         if user.dm_channel is None:
#             await user.create_dm()
#         await user.dm_channel.send("This is a direct message from me, Norfolk!")

client.run(secrets.token)