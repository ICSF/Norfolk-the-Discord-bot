import discord
import secrets
from asyncio import sleep
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
                            await self.channel.send("OK, you are a Member! **I've given you the role.**")
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
                            await self.channel.send("OK, you are a Member! **I've given you the role.**")
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
                     "purchase. Search your inbox for_ \"Your Order at Imperial College Union\" _to find it._"],
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


class VotingCon(Conversation):
    def __init__(self, dm_channel, vote):
        self.vote = vote
        self.steps = {
            "init": {
                "text": ["**" + "-" * 60 + "**\n\n"
                         "Hi! This is a vote on:```{}```Please type out your vote below and send it. It will be passed to "
                         "the Returning Officer.\n\nYour message can include other information, like abstaining, not voting"
                         ", or your proxy votes.".format(self.vote)],
                "interaction": {
                    "type": "input",
                    "store_as": "text",
                    "next": self.process_vote
                },
            },
        }
        super().__init__(dm_channel)

    async def finish(self, *args):
        await self.channel.send("Thanks for your vote!\n\n**"+"-"*60+"**")
        return None

    async def process_vote(self, *args):
        text = "Vote from {} on '{}': ```{}```".format(self.channel.recipient.mention, self.vote, self.text)
        await client.get_user(378887560119975939).send(text)
        return self.finish


cons = []

client = discord.Client()
icsf = None


@client.event
async def on_ready():
    global icsf
    print('We have logged in as {0.user}'.format(client))
    icsf = client.get_guild(430437751603724319)
    await client.change_presence(activity=discord.Game(name='sweet sweet democracy'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$egg'):
        await message.channel.send('EGG')
        await message.delete()

    if message.content.startswith('!eddify') or message.content.startswith('!ellify'):
        await message.channel.send(message.content[8:].replace("l", "#").replace("d", "l").replace("#", "d").replace("L", "#").replace("D", "L").replace("#", "D"))

    if message.content.startswith('!nsend') and message.author.guild_permissions.administrator:
        s = message.content.split(" ")
        channel = client.get_channel(int(s[1][2:-1]))
        contents = " ".join(s[2:])
        await channel.send(contents)

    if message.content.startswith('!nedit') and message.author.guild_permissions.administrator:
        s = message.content.split(" ")
        channel = client.get_channel(int(s[1][2:-1]))
        message = await channel.fetch_message(int(s[2]))
        contents = " ".join(s[3:])
        await message.edit(content=contents)

    if message.content.startswith('!playing') and message.author.guild_permissions.administrator:
        await client.change_presence(activity=discord.Game(name=message.content[8:]))

    if message.content.startswith('!agm_vote') and message.author.guild_permissions.administrator:
        embed = discord.Embed(
            title="This is a vote on:",
            description=message.content[10:],
            colour=discord.Colour.blue())
        m = await message.channel.send("Click the 🗳️ reaction below to vote, and check your direct message for a message from <@!767851328092766268>.", embed=embed)
        await m.add_reaction("🗳️")

    for con in [x for x in cons if message.channel == x.channel]:
        await con.receive(message)


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return

    if payload.message_id == 774771312983408681 and payload.event_type == "REACTION_ADD":
        user = client.get_user(payload.user_id)
        if user.dm_channel is None:
            await user.create_dm()
        con = MembershipCon(user.dm_channel)
        cons.append(con)
        await con.go()

    if payload.message_id == 774760325513216040 and payload.event_type == "REACTION_ADD":
        user = client.get_user(payload.user_id)
        await user.send("**"+"-"*60+"**\n\nThank you for scrolling up! The surprise is a picture of a cute dog and "
                                    "will be delivered promptly.\n\n"
                        "Fetching cute dog...")
        await sleep(5)
        await user.send("Retrieval complicated by the dog not liking Daleks. Retrying...")
        await sleep(4)
        await user.send("https://cdn.discordapp.com/attachments/767860174777614356/775475752941518878/277e031b-e366-43b3-9511-54a6df59ecd5.png")
        await user.send("There it is!")
        await sleep(2)
        await user.send("Now click this link to get back to role selection: "
                        "https://discord.com/channels/430437751603724319/767849852863643659/774760325513216040")

    if payload.channel_id == 824992986009829396 and payload.event_type == "REACTION_ADD":
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if len(message.embeds):
            embed = message.embeds[0]
            if payload.member.dm_channel is None:
                await payload.member.create_dm()
            con = VotingCon(payload.member.dm_channel, embed.description)
            cons.append(con)
            await con.go()

    for con in [x for x in cons if payload.channel_id == x.channel.id]:
        await con.reaction(payload)

client.run(secrets.token)
