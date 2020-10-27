import discord
import secrets
from aiohttp import ClientSession, BasicAuth


class Conversation:
    steps = {}

    def __init__(self, dm_channel):
        self.channel = dm_channel
        self._current = "init"

    async def go(self):
        if hasattr(self._current, '__call__'):
            self._current = await self._current(self)
            await self.go()

        else:
            if self._current is None:
                cons.remove(self)
                return

            step = self.steps[self._current]
            for message in step["text"]:
                m = await self.channel.send(message)
            if step["interaction"]["type"] == "reaction":
                for option in step["interaction"]["options"]:
                    await m.add_reaction(option)

    async def reaction(self, payload):
        interaction = self.steps[self._current]["interaction"]
        if interaction["type"] == "reaction" and payload.user_id == self.channel.recipient.id:
            for i in range(len(interaction["options"])):
                if interaction["options"][i] == str(payload.emoji):
                    self._current = interaction["next"][i]
                    await self.go()
                    return

    async def receive(self, message):
        interaction = self.steps[self._current]["interaction"]
        if interaction["type"] == "input" and message.author == self.channel.recipient:
            self.__setattr__(interaction["store_as"], message.content)
            self._current = interaction["next"]
            await self.go()

    def __repr__(self):
        return "Conversation({})".format(self.channel)


class MembershipCon(Conversation):
    async def finish(self, *args):
        await self.channel.send("Thanks for chatting!\n\n**"+"-"*60+"**")
        return None

    async def check_CID(self):
        if self.CID == "order":
            return "input_order"

        await self.channel.send("Thanks, let me check that...")
        async with ClientSession() as session:
            async with session.get('https://eactivities.union.ic.ac.uk/API/CSP/266/reports/members',
                                   auth=BasicAuth('user', secrets.eActivities)) as r:
                if r.status == 200:
                    js = await r.json()
                    for person in js:
                        if person["CID"] == self.CID:
                            await self.channel.send("Hi {}, you are a Member! **I've given you the role.**".format(person["FirstName"]))
                            member = await icsf.fetch_member(self.channel.recipient.id)
                            await member.add_roles(icsf.get_role(769685221695029258))
                            return self.finish
                    return "failure"

    async def check_order(self):
        await self.channel.send("Thanks, let me check that...")
        async with ClientSession() as session:
            async with session.get('https://eactivities.union.ic.ac.uk/API/CSP/266/reports/members',
                                   auth=BasicAuth('user', secrets.eActivities)) as r:
                if r.status == 200:
                    js = await r.json()
                    for person in js:
                        if str(person["OrderNo"]) == self.order.replace(" ", ""):
                            await self.channel.send("Hi {}, you are a Member! **I've given you the role.**".format(person["FirstName"]))
                            member = await icsf.fetch_member(self.channel.recipient.id)
                            await member.add_roles(icsf.get_role(769685221695029258))
                            return self.finish
                    return "failure"

    steps = {
        "init": {
            "text": ["**"+"-"*60+"**\n\n"
                     "Hi! In order to give you your **Member role** I will need a few details from you.\n"
                     "**Note:** if at any point during the process something breaks or you have questions, please "
                     "send a direct message to the Tech Priest, <@133647238235815936>.\n\nReady?\n"
                     "First, do you have a **current and valid CID** (College ID) number? Click "
                     "one of the reactions below to respond, ✅ for 'yes', and ❌ for 'no'."],
            "interaction": {
                "type": "reaction",
                "options": ["✅", "❌"],
                "next": ["input_CID", "input_order"]
            },
        },
        "input_CID": {
            "text": ["OK, please **type your CID** in the text field below and send it to me!\n"
                     "You can delete it from this chat once the verification process is complete, and we will use it "
                     "one time to **verify your membership** and then discard it.\n"
                     "If you prefer to provide us with your Union shop order number, type and send the word 'order'.\n"
                     "_The CID must include all the leading zeros, exactly as it is stated on your College card._"],
            "interaction": {
                "type": "input",
                "store_as": "CID",
                "next": check_CID,
            }
        },
        "input_order": {
            "text": ["OK, please **type your order number** in the text field below and send it to me!\n"
                     "You can delete it from this chat once the verification process is complete, and we will use it "
                     "one time to **verify your membership** and then discard it.\n"
                     "_You can find your order number in an email from the Union Shop confirming your membership "
                     "purchase. Search your inbox for 'Your Order at Imperial College Union' to find it._"],
            "interaction": {
                "type": "input",
                "store_as": "order",
                "next": check_order
            }
        },
        "failure": {
            "text": ["That didn't work :/ **Please make sure you've entered your CID/order number correctly**, and if "
                     "you think something's wrong with the process, "
                     "**message the Tech Priest, <@133647238235815936>**.\n\n"
                     "Would you like to try again?"],
            "interaction": {
                "type": "reaction",
                "options": ["✅", "❌"],
                "next": ["init", finish]
            }
        }
    }


cons = []

client = discord.Client()
icsf = None


votes = {}


@client.event
async def on_ready():
    global icsf
    print('We have logged in as {0.user}'.format(client))
    icsf = client.get_guild(430437751603724319)
    await client.change_presence(activity=discord.Game(name='just wanted to say hi'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # if message.content.startswith('$egg'):
    #     await message.channel.send('EGG')
    #     await message.delete()

    if message.content.startswith('!halloween_vote'):
        await message.delete()
        await message.channel.send("Voting has begun!\n\n**You have three votes:** 3 points, 2 points, and 1 point. "
                                   "Give them to 3 separate people! Or one person, if you _really_ want to.\n\n"
                                   "Click on the reactions below the posts to give the points.")
        global votes
        votes = {}
        async for m in message.channel.history(limit=100):
            await m.clear_reactions()
            await m.add_reaction("3️⃣")
            await m.add_reaction("2️⃣")
            await m.add_reaction("1️⃣")

    if message.content.startswith('!eddify') or message.content.startswith('!ellify'):
        await message.channel.send(message.content[8:].replace("l", "#").replace("d", "l").replace("#", "d").replace("L", "#").replace("D", "L").replace("#", "D"))

    for con in [x for x in cons if message.channel == x.channel]:
        await con.receive(message)


@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    emoji = reaction.emoji
    if message.channel.id == 770563414925246466:
        if user in votes and emoji in votes[user] and votes[user][emoji]:
            user.send("You can only give {} points to one user. Right now you've given it to <@{}>. In order to give "
                      "it to someone else you'll need to remove it from this message: {}.\n\nChoose wisely!".format(
                        emoji, message.author.id, message.jump_url
                      ))
            await reaction.remove()
        else:
            votes[user][reaction.emoji] = message


@client.event
async def on_reaction_remove(reaction, user):
    message = reaction.message
    if message.channel.id == 770563414925246466:
        votes[user][reaction.emoji] = None



@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == 769997390051672144 and payload.event_type == "REACTION_ADD":
        user = client.get_user(payload.user_id)
        if user.dm_channel is None:
            await user.create_dm()
        con = MembershipCon(user.dm_channel)
        cons.append(con)
        await con.go()

    for con in [x for x in cons if payload.channel_id == x.channel.id]:
        await con.reaction(payload)

client.run(secrets.token)