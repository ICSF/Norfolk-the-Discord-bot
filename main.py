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
    await client.change_presence(activity=discord.Game(name='ready for Halloween?'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # if message.content.startswith('$egg'):
    #     await message.channel.send('EGG')
    #     await message.delete()

    if message.content.startswith('!halloween_vote') and message.author.id == 133647238235815936:
        await message.delete()
        global votes
        votes = {}
        async for m in message.channel.history(limit=100):
            await m.clear_reactions()
            await m.add_reaction("3️⃣")
            await m.add_reaction("2️⃣")
            await m.add_reaction("1️⃣")
        await message.channel.send("Voting has begun!\n\n**You have three votes:** 3 points, 2 points, and 1 point.\n"
                                   "The total number of points will be summed up for each participant, and the "
                                   "winner chosen based on the sum of points they are given!\n\n"
                                   "Here are some rules:\n"
                                   "* Assign your points to 3 separate people.\n"
                                   "* You can only give each number of points once, for example only one person gets "
                                   "3️⃣ points from you.\n"
                                   "* You cannot vote for yourself.\nIf your reaction is removed, it will be for "
                                   "violating one of these rules - look out for a direct message from "
                                   "<@767851328092766268> with an explanation!\n\n"
                                   "**Click on the reactions below the posts to assign the points.** Click again to "
                                   "remove them if you change your mind.")

    if message.content.startswith('!halloween_count') and message.author.id == 133647238235815936:
        await message.delete()
        totals = {}
        for voter in votes.keys():
            for points in votes[voter].keys():
                p = int(points[0])
                if votes[voter][points] is None:
                    continue
                human = votes[voter][points].author
                if human in totals:
                    totals[human] += p
                else:
                    totals[human] = p
        text = "**"+"-"*60+"**\n"+"**Here are our SPOOKY winners!**\n\n"
        i = 0
        prev_score = 0
        for user, score in sorted(totals.items(), key=lambda item: item[1], reverse=True):
            if score != prev_score:
                i += 1
            text += "{}. <@{}> - {} points\n".format(i, user.id, score)
            prev_score = score
        await message.channel.send(text)

    if message.content.startswith('!eddify') or message.content.startswith('!ellify'):
        await message.channel.send(message.content[8:].replace("l", "#").replace("d", "l").replace("#", "d").replace("L", "#").replace("D", "L").replace("#", "D"))

    for con in [x for x in cons if message.channel == x.channel]:
        await con.receive(message)


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

    if (
            payload.channel_id == 770563414925246466 and
            payload.user_id != 767851328092766268 and
            str(payload.emoji) in ("3️⃣", "2️⃣", "1️⃣")
    ):
        message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
        user = client.get_user(payload.user_id)
        emoji = str(payload.emoji)
        if user.id in votes and emoji in votes[user.id] and votes[user.id][emoji]:
            await message.remove_reaction(emoji, user)
            await user.send("**"+"-"*60+"**\n"
                            "You can only give {} points to one user. Right now you've given it to <@{}>. In order to "
                            "give it to someone else you'll need to remove it from this message: "
                            "https://discord.com/channels/430437751603724319/770563414925246466/{}.\n\n"
                            "Choose wisely!".format(
                                emoji, votes[user.id][emoji].author.id, votes[user.id][emoji].id
                            ))
        elif user.id in votes and message in [votes[user.id][x] for x in ("3️⃣", "2️⃣", "1️⃣") if x in votes[user.id]]:
            await message.remove_reaction(emoji, user)
            await user.send("**" + "-" * 60 + "**\n"
                            "You can only give one reaction to each user. You've already given some points to <@{}>.\n"
                            "Share them with others!\n\n"
                            "Remember that you can change your mind and remove reactions until the "
                            "voting closes!".format(message.author.id))
        elif user.id == message.author.id:
            await message.remove_reaction(emoji, user)
            await user.send("**"+"-"*60+"**\n"
                            "Please don't vote for yourself, that's no fun!")
        else:
            if user.id not in votes:
                votes[user.id] = {}
            print("{} voted for {}".format(user.id, message.id))
            votes[user.id][emoji] = message

        # print(votes)

    for con in [x for x in cons if payload.channel_id == x.channel.id]:
        await con.reaction(payload)


@client.event
async def on_raw_reaction_remove(payload):
    # print(payload)
    if (
            payload.channel_id == 770563414925246466 and
            payload.user_id != 767851328092766268 and
            str(payload.emoji) in ("3️⃣", "2️⃣", "1️⃣")
    ):
        if (
            payload.user_id in votes and
            str(payload.emoji) in votes[payload.user_id] and
            votes[payload.user_id][str(payload.emoji)] and
            votes[payload.user_id][str(payload.emoji)].id == payload.message_id
        ):
            votes[payload.user_id][str(payload.emoji)] = None


client.run(secrets.token)