import discord
import secrets
from asyncio import sleep
from aiohttp import ClientSession, BasicAuth
import sqlite3


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


cons = []

client = discord.Client()
icsf = None

# Some April constants
values = {
    "0": 13, "1": 3, "2": 6, "3": 8, "4": 7, "5": 10, "6": 10,
    "7": 8, "8": 9, "9": 4,
    "a": 1, "A": 1.5, "b": 0.5, "B": 1, "c": 4, "C": 4.5, "d": -4, "D": -4.5, "e": 6.9, "E": 7.4,
    "f": 0, "F": 15, "g": 9, "G": 9.5, "h": 6.63, "H": 7.13, "i": -1, "I": -1.5, "j": 3, "J": 3.5,
    "k": -3.14, "K": -3.64, "l": -10, "L": -15, "m": 5, "M": 5.5, "n": 2.05, "N": -2.55, "o": 0, "O": 0,
    "p": 2.34, "P": 2.84, "q": 7.25, "Q": 7.75, "r": -3, "R": -3.5, "s": -5, "S": -5.5, "t": 5.17, "T": 5.67,
    "u": 10, "U": 10.5, "v": 5, "V": 5.5, "w": 10, "W": 10.5, "x": 10, "X": 10.5, "y": 5, "Y": -5.5, "z": 1, "Z": 1.5,
    ",": 1.23, ".": -5, ":": 3, ";": 30, "?": 5.6, "!": -10, "&": 8, "%": 100, "*": 6.54, "<": -1, ">": 1,
}


async def april_board(client, channel):
    cursor = client.dbconn.execute("SELECT * FROM users ORDER BY total DESC LIMIT 9")
    text = ""

    for i, row in enumerate(cursor):
        text += "{}. {} (**{:.2f}points**)\n".format(i + 1, row["mention"], row["total"])

    text += "...\n"
    cursor = client.dbconn.execute("SELECT count(id) AS i FROM users")
    row = cursor.fetchone()
    i = row["i"]-9

    cursor = client.dbconn.execute("SELECT * FROM (SELECT * FROM users ORDER BY total ASC LIMIT 9) ORDER BY total DESC")
    for row in cursor:
        text += "{}. {} (**{:.2f}points**)\n".format(i + 1, row["mention"], row["total"])
        i += 1

    embed = discord.Embed(title="The AprilBoard", description=text,
                          colour=discord.Colour.from_rgb(135, 169, 224))
    embed.set_thumbnail(url="https://i.imgur.com/mJ7zu6k.png")
    await channel.send(embed=embed)


@client.event
async def on_ready():
    global icsf

    client.dbconn = sqlite3.connect('main.db')
    client.dbconn.row_factory = sqlite3.Row
    client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "users" (
                             "id" INTEGER UNIQUE,
                             "user_id" INTEGER UNIQUE,
                             "mention" TEXT,
                             "username" TEXT,
                             "total" NUMERIC DEFAULT 0,
                             PRIMARY KEY("id" AUTOINCREMENT)
                             );''')
    client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "words" (
                             "id" INTEGER UNIQUE,
                             "word" TEXT,
                             "quality" NUMERIC,
                             PRIMARY KEY("id" AUTOINCREMENT)
                             );''')

    print('We have logged in as {0.user}'.format(client))
    icsf = client.get_guild(430437751603724319)
    await client.change_presence(activity=discord.Game(name='just wanted to say hi'))


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

    # April Fools functionality
    if message.content.startswith('!april_init') and message.author.guild_permissions.administrator:
        await message.channel.send("Initialising Operation April...")
        async for member in icsf.fetch_members():
            string_id = str(member.id)
            score = sum([values[x] for x in string_id])
            client.dbconn.execute("INSERT OR IGNORE INTO users (user_id, total, mention, username) VALUES (?, ?, ?, ?)",
                                  (member.id, score, member.mention, member.name))
        client.dbconn.commit()
        await message.channel.send("Much init, such done.")

    if message.content.startswith('!aprilboard') and message.author.guild_permissions.administrator:
        await april_board(client, message.channel)

    if message.content.startswith('!april'):
        # TODO: remove points on check

        cursor = client.dbconn.execute("SELECT total FROM users WHERE user_id=133647238235815936")
        row = cursor.fetchone()
        text = "You have **{:.2f}** points, {}.".format(row["total"], message.author.mention)

        embed = discord.Embed(description=text,
                              colour=discord.Colour.from_rgb(135, 169, 224))
        embed.set_footer(text="This check has a cost.")
        await message.channel.send(embed=embed)

    if not message.content.startswith('!') and message.channel.id == 826925077580742666:
        spaces = message.content.count(" ")
        score = sum([values[x] for x in message.content if x in values]) / (spaces if spaces else 0.5)

        client.dbconn.execute("UPDATE users SET total = total + ? WHERE user_id = ?", (score, message.author.id))
        client.dbconn.commit()

        if message.channel.id == 826925077580742666:
            await message.channel.send(score)

    # Conversations
    for con in [x for x in cons if message.channel == x.channel]:
        await con.receive(message)


@client.event
async def on_raw_reaction_add(payload):
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

    for con in [x for x in cons if payload.channel_id == x.channel.id]:
        await con.reaction(payload)

client.run(secrets.token)
