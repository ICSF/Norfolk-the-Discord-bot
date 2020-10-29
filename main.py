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


async def construct_votes(message):
    print("Getting the votes...")
    votes = {}
    async for m in message.channel.history(limit=100):
        for reaction in m.reactions:
            emoji = str(reaction.emoji)
            if emoji in ("3️⃣", "2️⃣", "1️⃣"):
                users = await reaction.users().flatten()
                for user in users:
                    if user not in votes:
                        votes[user] = {}
                    if emoji not in votes[user]:
                        votes[user][emoji] = [m]
                    else:
                        votes[user][emoji].append(m)
    return votes


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
                                   "* You cannot vote for yourself.\nWe will be checking the votes for compliance "
                                   "with these rules and will let you know if you make a mistake!\n\n"
                                   "**Click on the reactions below the posts to assign the points.** Click again to "
                                   "remove them if you change your mind.")

    if message.content.startswith('!halloween_enforce') and message.author.id == 133647238235815936:
        dm = len(message.content.split(" ")) <= 1
        await message.delete()
        # Get all of the votes
        votes = await construct_votes(message)
        scores = {}
        # Make a list of users who have violated some rules
        violations = []

        # Go through each person who voted
        for user in votes.keys():
            # Don't worry about Norfolk
            if user.id == 767851328092766268:
                continue
            # This list stores messages seen so far
            seen = []
            # Go through the different applicable emoji
            for emoji in votes[user].keys():
                # More than one vote per emoji
                if len(votes[user][emoji]) > 1:
                    print(user, emoji, "violation")
                    text = "**" + "-" * 60 + "**\n"+"You can only give {} points to one user. Right now you've given " \
                           "it to these messages:\n* ".format(emoji)
                    text += "\n* ".join(["<@" + str(vote.author.id) + ">: " + vote.jump_url for vote in votes[user][emoji]])
                    text += "\n\n **Please remove some of these so that only one remains, otherwise your votes " \
                            "won't count!**"
                    if dm:
                        await user.send(text)
                    print([vote.jump_url for vote in votes[user][emoji]])
                    if user not in violations:
                        violations.append(user)

                # Go through votes for a particular emoji
                for vote in votes[user][emoji]:
                    # Voting for self
                    if vote.author == user:
                        print(user, "self-voting")
                        if user not in violations:
                            violations.append(user)
                        if dm:
                            await user.send("**" + "-" * 60 + "**\n"
                                            "Please don't vote for yourself, that's no fun! \n\n Remove the reaction "
                                            "from {}.".format(vote.jump_url))

                    # More than one vote per message
                    if vote in seen:
                        print(user, "more-than-one")
                        if user not in violations:
                            violations.append(user)
                        if dm:
                            await user.send("**" + "-" * 60 + "**\n"
                                            "You can only give one reaction to each user. You've given too many points "
                                            "to <@{}>.\n"
                                            "Share them with others!\n\n"
                                            "Please remove some votes from {}.".format(vote.author.id, vote.jump_url))
                        print(vote.jump_url)
                seen.extend(votes[user][emoji])
            # If no violations for the user, count their votes
            if user not in violations:
                for emoji in votes[user].keys():
                    points = int(emoji[0])
                    author = votes[user][emoji][0].author
                    if author not in scores:
                        scores[author] = points
                    else:
                        scores[author] += points
        # Send a summary of votes
        text = "**Here are our SPOOKY winners!**\n\n"
        i = 0
        prev_score = 0
        for user, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            if score != prev_score:
                i += 1
            text += "{}. <@{}>: {} points\n".format(i, user.id, score)
            prev_score = score
        await client.get_channel(689605126465388552).send(text)

        if len(violations):
            text = "Some voting mistakes have been made by <@"
            text += ">, <@".join([str(u.id) for u in violations])
            text += ">.\n\nPlease check your direct messages for details."
            await message.channel.send(text)
        else:
            await message.channel.send("No voting mistakes were made!")

    if message.content.startswith('!eddify') or message.content.startswith('!ellify'):
        await message.channel.send(message.content[8:].replace("l", "#").replace("d", "l").replace("#", "d").replace("L", "#").replace("D", "L").replace("#", "D"))

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