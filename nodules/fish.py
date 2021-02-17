from . import CoreNodule
from discord import Embed, Colour
import random


class Nodule(CoreNodule):
    def __init__(self, client):

        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "fish" (
                                 "id" INTEGER UNIQUE,
                                 "name" TEXT,
                                 "pic" TEXT,
                                 "description" TEXT,
                                 "attack" NUMERIC,
                                 "defence" NUMERIC,
                                 "price" NUMERIC,
                                 "message_id" INTEGER,
                                 PRIMARY KEY("id" AUTOINCREMENT)
                                 );''')
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "hp" (
                                       "id" INTEGER UNIQUE,
                                       "user_id" INTEGER UNIQUE,
                                       "total" NUMERIC DEFAULT 100,
                                       PRIMARY KEY("id" AUTOINCREMENT)
                                       );''')
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "fish_ownership" (
                                 "id" INTEGER UNIQUE,
                                 "owner" INTEGER,
                                 "fish" INTEGER,
                                 "quality" NUMERIC DEFAULT 1,
                                 PRIMARY KEY("id" AUTOINCREMENT),
                                 FOREIGN KEY("fish") REFERENCES "fish"("id"),
                                 FOREIGN KEY("owner") REFERENCES "hp"("id")
                                 );''')

        super().__init__(client)

    async def on_message(self, message):
        if message.content.startswith('!_fishmarket') and message.author.guild_permissions.administrator:
            channel = message.channel
            await message.delete()
            cursor = self.client.dbconn.execute("SELECT * FROM fish")
            for row in cursor:
                embed = Embed(title=row["name"], description=row["description"], colour=Colour.from_rgb(135, 169, 224))
                embed.set_thumbnail(url=row["pic"])
                embed.add_field(name="Attack", value=row["attack"])
                embed.add_field(name="Defence", value=row["defence"])
                embed.add_field(name="Price", value="{:.2f} <:picocoin:810623980222021652>".format(row["price"]))
                m = await channel.send(embed=embed)
                await m.add_reaction("⬆️")
                self.client.dbconn.execute("UPDATE fish SET message_id=(?) WHERE id=?", (m.id, row["id"]))
                self.client.dbconn.commit()

        if message.content.startswith('!fish'):
            self.ensure_fish(message.author.id)
            await self.fish_arsenal(message.channel, message.author.id)

        if message.content.startswith('!slap'):
            if message.channel.id != 810500594962923521:
                embed = Embed(title="Have some decency!",
                              description="Fish slapping is only permitted in <#810500594962923521>.",
                              colour=Colour.red())
                await message.channel.send(embed=embed)
                return

            self.ensure_fish(message.author.id)
            try:
                _, user, = message.content.split(" ")
                target_id = user[3:-1]
            except ValueError:
                embed = Embed(title="Incorrect argument",
                              description="The syntax is `!slap <user mention>`\nFor example: !slap <@!810233904506077205>",
                              colour=Colour.red())
                await message.channel.send(embed=embed)
                return
            self.ensure_fish(target_id)

            # Get the attack stats
            text = "```{:>15} | {:>7} | {:>6}\n".format("Fish", "Quality", "Attack", "Defence")
            text += "-" * 34 + "\n"
            cursor = self.client.dbconn.execute(
                "SELECT name, quality, attack, defence, hp.id FROM fish_ownership INNER JOIN hp ON hp.id = fish_ownership.owner INNER JOIN fish ON fish.id=fish_ownership.fish WHERE hp.user_id=?",
                (message.author.id,))
            attack = 0
            for row in cursor:
                text += "{:>15} |    {:01.2f} | {:6.2f}\n".format(row["name"], row["quality"],
                                                                  row["attack"] * row["quality"])
                attack += row["attack"] * row["quality"]
            user_id = row["id"]
            text += "-" * 34 + "\n"
            text += " " * 28 + "{:6.2f}".format(attack)
            text += "```\n"
            cursor = self.client.dbconn.execute("SELECT SUM(defence*quality) as d FROM fish_ownership INNER JOIN hp ON hp.id = fish_ownership.owner INNER JOIN fish ON fish.id=fish_ownership.fish WHERE hp.user_id=?",
                                                (target_id,))
            defence = cursor.fetchone()["d"]
            text += ":shield: The target has **{:.2f} defence**.\n\n".format(defence)

            text += "`(2d20 + attack) - (d20 + opponent's defence)`\n"
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            c = random.randint(1, 20)
            text += "`({}+{} + {:.2f}) - ({} + {:.2f})`\n".format(a, b, attack, c, defence)
            total = (a+b+attack) - (c+defence)
            total = total if total>0 else 0
            text += "`{:.2f}` **damage!**\n\n".format(total)

            # Take away the damage
            self.client.dbconn.execute("UPDATE hp SET total = total - ? WHERE user_id = ?", (total, target_id))
            self.client.dbconn.commit()
            cursor = self.client.dbconn.execute("SELECT total FROM hp WHERE user_id=?", (target_id,))
            hp = cursor.fetchone()["total"]
            text += ":heart: <@{}> has **{:.2f}HP** now.".format(target_id, hp)

            # Decrease fish quality
            self.client.dbconn.execute("UPDATE fish_ownership SET quality=quality*0.9 WHERE owner = ?", (user_id,))
            self.client.dbconn.commit()

            # Send the message
            embed = Embed(description=text,
                          colour=Colour.from_rgb(135, 169, 224))
            await message.channel.send("<@{}> slaps <@{}> with their fish!".format(message.author.id, target_id), embed=embed)



    def ensure_fish(self, user_id):
        self.client.dbconn.execute("INSERT OR IGNORE INTO hp (user_id) VALUES (?)", (user_id,))
        self.client.dbconn.commit()
        cursor = self.client.dbconn.execute(
            "SELECT * FROM fish_ownership INNER JOIN hp on fish_ownership.owner=hp.id WHERE hp.user_id=?",
            (user_id,)
        )
        if not cursor.fetchone():
            cursor = self.client.dbconn.execute("SELECT id FROM hp WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            self.client.dbconn.execute("INSERT INTO fish_ownership (owner, fish) VALUES (?, 1)", (row["id"],))
            self.client.dbconn.commit()

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == 810500564395098142:
            cursor = self.client.dbconn.execute("SELECT * FROM fish WHERE message_id=?", (payload.message_id,))
            user = self.client.get_user(payload.user_id)
            row = cursor.fetchone()
            if row:
                try:
                    total = self.client.picocoin.take(payload.user_id, row["price"])
                except ValueError:
                    total = self.client.picocoin.check(payload.user_id)
                    embed = Embed(
                        description="**You don't have enough Picocoin to purhcase this fish.** You have {:.2f}, but you need {:.2f}.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                            total, row["price"]
                        ),
                        colour=Colour.red())
                    await user.send(embed=embed)
                    return
                cursor = self.client.dbconn.execute("SELECT id FROM hp WHERE user_id=?", (payload.user_id,))
                owner_id = cursor.fetchone()["id"]
                self.client.dbconn.execute("INSERT INTO fish_ownership (owner, fish) VALUES (?, ?)", (owner_id, row["id"]))
                self.client.dbconn.commit()
                embed = Embed(
                    description="**You have purchased {} for {:.2f} Picocoin.** You have {:.2f} Picocoin remaining.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                        row["name"], row["price"], total
                    ),
                    colour=Colour.green())
                await user.send(embed=embed)
                await self.fish_arsenal(user, user.id)

    async def fish_arsenal(self, channel, user_id):
        text = "{:>15} | {:>4} | {:>6} | {:>7}\n".format("Fish", "Qual", "Attack", "Defence")
        text += "-"*41+"\n"
        cursor = self.client.dbconn.execute("SELECT name, quality, attack, defence FROM fish_ownership INNER JOIN hp ON hp.id = fish_ownership.owner INNER JOIN fish ON fish.id=fish_ownership.fish WHERE hp.user_id=?",
                                            (user_id,))
        attack = defence = 0
        for row in cursor:
            text += "{:>15} | {:01.2f} | {:6.2f} | {:7.2f}\n".format(row["name"], row["quality"], row["attack"]*row["quality"], row["defence"]*row["quality"])
            attack += row["attack"]*row["quality"]
            defence += row["defence"]*row["quality"]
        text += "-" * 41 + "\n"
        text += " "*25 + "{:6.2f} | {:7.2f}".format(attack, defence)
        embed = Embed(title="Your fish arsenal",
                      description="```{}```".format(text),
                      colour=Colour.from_rgb(135, 169, 224))
        await channel.send(embed=embed)
