import discord
import secrets
from aiohttp import ClientSession, BasicAuth


class Conversation:
    steps = {}

    def __init__(self, dm_channel):
        self.channel = dm_channel
        self._current = "init"

    async def go(self):
        print(self._current)
        if hasattr(self._current, '__call__'):
            self._current = await self._current(self)

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
                    print(self._current)
                    await self.go()
                    return

    async def receive(self, message):
        interaction = self.steps[self._current]["interaction"]
        if interaction["type"] == "input" and message.author == self.channel.recipient:
            self.__setattr__(interaction["store_as"], message.content)
            if interaction["delete"]:
                await message.delete()
            self._current = interaction["next"]
            await self.go()

    def __repr__(self):
        return "Conversation({})".format(self.channel)


class MembershipCon(Conversation):
    async def check_CID(self):
        await self.channel.send("Thanks, let me check that...")
        async with ClientSession() as session:
            async with session.get('https://eactivities.union.ic.ac.uk/API/CSP/266/reports/members',
                                   auth=BasicAuth('user', secrets.eActivities)) as r:
                if r.status == 200:
                    js = await r.json()
                    for person in js:
                        if person["CID"] == self.CID:
                            await self.channel.send("Hi {}, you are a Member!".format(person["FirstName"]))
                            member = await icsf.fetch_member(self.channel.recipient.id)
                            await member.add_roles(icsf.get_role(769685221695029258))
                            return "member_confirmed"
                    return "failure"

    steps = {
        "init": {
            "text": ["Hi! In order to give you your **Member role** I will need a few details from you.\n"
                     "**Note:** if at any point during the process something breaks or you have questions, please "
                     "send a direct message to the Tech Priest, <@133647238235815936>.\n\nReady?\n"
                     "First, do you have a **current and valid CID** (College ID) number? Click "
                     "one of the reactions below to respond, ✅ for 'yes', and ❌ for 'no'."],
            "interaction": {
                "type": "reaction",
                "options": ["✅", "❌"],
                "next": ["input_CID", "input_purchase"]
            },
        },
        "input_CID": {
            "text": ["OK, please **type your CID** in the text field below and send it to me!\n"
                     "You can delete it from this chat once the verification process is complete, and we will use it"
                     "one time to **verify your membership** and then discard it.\n"
                     "_This must include all the leading zeros, exactly as it is stated on your College card._"],
            "interaction": {
                "type": "input",
                "delete": True,
                "store_as": "CID",
                "next": check_CID,
            }
        },
    }


cons = []

client = discord.Client()
icsf = None


@client.event
async def on_ready():
    global icsf
    print('We have logged in as {0.user}'.format(client))
    icsf = client.get_guild(430437751603724319)
    print(await icsf.fetch_member(133647238235815936))
    await client.change_presence(activity=discord.Game(name='just wanted to say hi'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    for con in [x for x in cons if message.channel == x.channel]:
        await con.receive(message)


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