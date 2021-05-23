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
    """
    Get the total amount of money raised in the fundraiser.
    """
    async with ClientSession() as session:
        async with session.get(url + 'fundraising/pages/{}'.format(fundraiser), headers={"Accept": "application/json"},
                               auth=BasicAuth(username, password)) as r:
            if r.status == 200:
                js = await r.json()
                return float(js["totalRaisedOnline"])


async def get_donations():
    """
    Get the number and list of donations.
    """
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
                               "total" NUMERIC DEFAULT 1,
                               PRIMARY KEY("id" AUTOINCREMENT)
                               );''')

    def check(self, user_id):
        # Check the balance of a user, creating their entry id none
        self.dbconn.execute("INSERT OR IGNORE INTO picocoin (user_id) VALUES (?)", (user_id,))
        self.dbconn.commit()
        return float(self.dbconn.execute("SELECT total FROM picocoin WHERE user_id=?", (user_id,)).fetchone()["total"])

    def give(self, user_id, amount):
        # Give user Picocoin
        total = self.check(user_id)
        self.dbconn.execute("UPDATE picocoin SET total = total + ? WHERE user_id = ?", (amount, user_id))
        self.dbconn.commit()
        return total + amount

    def take(self, user_id, amount):
        # Take Picocoin from the user, can't go below 0
        total = self.check(user_id)
        if total - amount >= 0:
            self.dbconn.execute("UPDATE picocoin SET total = total + ? WHERE user_id = ?", (-amount, user_id))
            self.dbconn.commit()
            return total - amount
        else:
            raise ValueError("The final amount is smaller than 0.")


class Nodule(CoreNodule):
    def __init__(self, client):

        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "donations_info" (
                                 "id" INTEGER UNIQUE,
                                 "total" NUMERIC,
                                 PRIMARY KEY("id" AUTOINCREMENT)
                                 );''')
        client.dbconn.execute("INSERT OR IGNORE INTO donations_info (id) VALUES (1)")
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "donations_processed" (
                                         "id" INTEGER UNIQUE,
                                         "donation_id" INTEGER,
                                         PRIMARY KEY("id" AUTOINCREMENT)
                                         );''')
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
                total = self.client.picocoin.give(user[3:-1], float(amount))
                embed = Embed(description="<:picocoin:810623980222021652> {} was given **{:.2f} Picocoin**. They now have **{:.2f} Picocoin**.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                    user, float(amount), total
                  ),
                  colour=Colour.green())
                await message.channel.send(embed=embed)
            except ValueError:
                total = self.client.picocoin.check(user[3:-1])
                embed = Embed(description="<:picocoin:810623980222021652> Please provide a valid amount. {} has {:.2f} Picocoin.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                    user, total
                  ),
                  colour=Colour.red())
                await message.channel.send(embed=embed)

        if message.content.startswith('!take') and message.author.guild_permissions.administrator:
            _, user, amount, = message.content.split(" ")
            try:
                total = self.client.picocoin.take(user[3:-1], float(amount))
                embed = Embed(description="<:picocoin:810623980222021652> {} has paid **{:.2f} Picocoin**. They now have **{:.2f} Picocoin**.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                    user, float(amount), total
                ),
                    colour=Colour.green())
                await message.channel.send(embed=embed)
            except ValueError:
                total = self.client.picocoin.check(user[3:-1])
                embed = Embed(
                    description="<:picocoin:810623980222021652> Please provide a valid amount. {} has {:.2f} Picocoin.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                        user, total
                    ),
                    colour=Colour.red())
                await message.channel.send(embed=embed)

        if message.content.startswith('!picocoin'):
            total = self.client.picocoin.check(message.author.id)
            embed = Embed(description="<:picocoin:810623980222021652> You ({}) have **{:.2f} Picocoin**.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(message.author.mention, total),
                colour=Colour.green())
            await message.channel.send(embed=embed)

        if message.content.startswith('!balance') and message.author.guild_permissions.administrator:
            _, user,  = message.content.split(" ")
            total = self.client.picocoin.check(user[3:-1])
            embed = Embed(description="<:picocoin:810623980222021652> {} has **{:.2f} Picocoin**.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(user, total),
                          colour=Colour.green())
            await message.channel.send(embed=embed)

    @loop(seconds=10)
    async def get_donations(self, message=None):
        donations = await self.donations()
        if donations:
            cursor = self.client.dbconn.execute("SELECT donation_id FROM donations_processed")
            processed = [row["donation_id"] for row in cursor]
            members = await self.client.picoguild.fetch_members(limit=150).flatten()
            for donation in donations:
                if donation["id"] in processed:
                    continue
                if donation["thirdPartyReference"]:
                    async with ClientSession() as session:
                        async with session.get('https://www.union.ic.ac.uk/scc/icsf/donate/get.php?id={}'.format(donation["thirdPartyReference"])) as r:
                            if r.status == 200:
                                username = await r.text()
                                if username:
                                    try:
                                        member = [x for x in members if (x.name+"#"+x.discriminator)==username][0]
                                        self.client.dbconn.execute("INSERT INTO donations_processed (donation_id) VALUES (?)", (donation["id"],))
                                        total = self.client.picocoin.give(member.id, float(donation["amount"]))
                                        await self.client.get_channel(810297672510472243).send(
                                            "<@{}> donated, and got {:.2f} Picocoin! Their total is now {:.2f} Picocoin.".format(
                                                member.id, float(donation["amount"]), total
                                            )
                                        )
                                    except IndexError:
                                        continue


    async def donations(self, message=None):
        total = await get_total()
        if total is None:
            return

        # Do things only if total changed, unless otherwise requested
        if not message:
            cursor = self.client.dbconn.execute("SELECT total FROM donations_info")
            row = cursor.fetchone()
            if row is not None and row["total"] is not None and float(row["total"]) >= total:
                return
            self.client.dbconn.execute("UPDATE donations_info SET total=(?) WHERE id=1", (total,))
            self.client.dbconn.commit()

        number, donations = await get_donations()
        embed = Embed(title="Charity donations", description="Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/",
                      colour=Colour.from_rgb(202, 138, 0))
        if message:
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/808080178965381171/810481381971853312/picocoin.gif")
        else:
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/808080178965381171/810496226322808892/0008.png")
        embed.add_field(name="Total donated", value="£{:.2f}".format(total))
        embed.add_field(name="Donations", value=number)
        if message:
            await message.channel.send(embed=embed)
        else:
            await self.client.get_channel(810297672510472243).send(embed=embed)
        return donations