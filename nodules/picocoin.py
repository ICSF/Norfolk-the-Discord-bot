from . import CoreNodule
from discord import Embed, Colour
from discord.ext.tasks import loop
from aiohttp import ClientSession, BasicAuth

app_key = "app_key"
url = "https://api.staging.justgiving.com/{}/v1/".format(app_key)
fundraiser = "save-endors-forests"
username = "email"
password = "password"


async def get_total():
    async with ClientSession() as session:
        async with session.get(url + 'fundraising/pages/{}'.format(fundraiser), headers={"Accept": "application/json"},
                               auth=BasicAuth(username, password)) as r:
            if r.status == 200:
                js = await r.json()
                return float(js["totalRaisedOnline"])


async def get_donations():
    async with ClientSession() as session:
        async with session.get(url + 'fundraising/pages/{}/donations'.format(fundraiser), headers={"Accept": "application/json"},
                               auth=BasicAuth(username, password)) as r:
            if r.status == 200:
                js = await r.json()
                return js["pagination"]["totalResults"], js["donations"]


class Picocoin:
    def __init__(self, dbconn):
        self.dbconn = dbconn
        self.dbconn.execute('''CREATE TABLE IF NOT EXISTS "picocoin" (
                               "id" INTEGER UNIQUE,
                               "user_id" INTEGER UNIQUE,
                               "total" NUMERIC DEFAULT 0,
                               PRIMARY KEY("id" AUTOINCREMENT)
                               );''')

    def ensure(self, user_id):
        self.dbconn.execute("INSERT OR IGNORE INTO picocoin (user_id) VALUES (?)", (user_id,))
        self.dbconn.commit()

    def give(self, user_id, amount):
        self.ensure(user_id)
        self.dbconn.execute("UPDATE picocoin SET total = total + ? WHERE user_id = ?", (amount, user_id))
        self.dbconn.commit()

    def take(self, user_id, amount):
        self.take(user_id, -amount)



class Nodule(CoreNodule):
    def __init__(self, client):

        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "donations_info" (
                                 "id" INTEGER UNIQUE,
                                 "total" NUMERIC,
                                 PRIMARY KEY("id" AUTOINCREMENT)
                                 );''')
        client.dbconn.execute("INSERT OR IGNORE INTO donations_info (id) VALUES (1)")
        client.dbconn.commit()

        client.picocoin = Picocoin(client.dbconn)

        super().__init__(client)
        self.get_donations.start()

    async def on_message(self, message):
        if message.content.startswith('!donations'):
            await self.donations(message)

        if message.content.startswith('!give') and message.author.guild_permissions.administrator:
            _, user, amount, = message.content.split(" ")
            try:
                self.client.picocoin.give(user[3:-1], float(amount))
            except ValueError:
                await message.channel.send("Please provide a valid amount.")

    async def on_raw_reaction_add(self, payload):
        pass

    @loop(seconds=30)
    async def get_donations(self, message=None):
        donations = await self.donations()

    async def donations(self, message=None):
        total = await get_total()

        # Do things only if total changed, unless otherwise requested
        if not message:
            cursor = self.client.dbconn.execute("SELECT total FROM donations_info")
            row = cursor.fetchone()
            if row is not None and float(row["total"]) == total:
                return
            self.client.dbconn.execute("UPDATE donations_info SET total=(?) WHERE id=1", (total,))
            self.client.dbconn.commit()

        number, donations = await get_donations()
        embed = Embed(title="Charity donations", description="Donate now at https://icsf.org.uk/donate",
                      colour=Colour.from_rgb(202, 138, 0))
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/808080178965381171/810481381971853312/picocoin.gif")
        embed.add_field(name="Total donated", value="£{:.2f}".format(total))
        embed.add_field(name="Donations", value=number)
        if message:
            await message.channel.send(embed=embed)
        else:
            await self.client.get_channel(810297672510472243).send(embed=embed)
        return donations
