from . import CoreNodule
from discord import Embed, Colour


def format_time(minutes):
    return "{:d}:{:02d}".format(int(minutes), int((minutes % 1)*60))

class Nodule(CoreNodule):
    def __init__(self, client):
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "talks" (
                                 "id" INTEGER UNIQUE,
                                 "message_id" INTEGER,
                                 "time" NUMERIC,
                                 "price" NUMERIC,
                                 "increment" NUMERIC,
                                 PRIMARY KEY("id" AUTOINCREMENT)
                                 );''')
        super().__init__(client)

    async def on_message(self, message):
        if message.content.startswith('!talk') and message.author.guild_permissions.administrator:
            # Parse arguments
            try:
                _, time, price, increment, *desc = message.content.split(" ")
                time = float(time)
                price = float(price)
                increment = float(increment)
            except ValueError:
                embed = Embed(
                    description="**Syntax error.** The syntax is `!talk <time> <price> <increment> <description>`",
                    colour=Colour.red())
                await message.channel.send(embed=embed)
                return

            # Generate the embed
            embed = Embed(title="Charity Talk", description=" ".join(desc), colour=Colour.blurple())
            embed.add_field(name="Duration:", value=format_time(time))
            embed.add_field(name="Price:", value="**{:.2f}**<:picocoin:810623980222021652> per **{}**".format(price, format_time(increment)))
            m = await self.client.get_channel(810500841059516457).send(embed=embed)

            # Insert into the database
            self.client.dbconn.execute("INSERT INTO talks (message_id, time, price, increment) VALUES (?, ?, ?, ?)",
                                       (m.id, time, price, increment))
            self.client.dbconn.commit()

            # Add reactions
            await m.add_reaction("🔺")
            await m.add_reaction("🔻")

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == 810500841059516457 and (payload.emoji.name=="🔺" or payload.emoji.name=="🔻"):
            channel = self.client.get_channel(810500841059516457)
            cursor = self.client.dbconn.execute("SELECT * FROM talks WHERE message_id=?", (payload.message_id,))
            row = cursor.fetchone()
            if row:
                message = await channel.fetch_message(payload.message_id)
                embed = message.embeds[0]
                total = self.client.picocoin.check(payload.user_id)
                if total < row["price"]:
                    await channel.send("<@{}> You don't have enough Picocoin to impact this talk, you have {:.2f}, but you have {:.2f}.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                        payload.user_id, total, row["price"]
                    ))
                    return
                total = self.client.picocoin.take(payload.user_id, row["price"])

                increment = row["increment"]
                increment *= 1 if payload.emoji.name=="🔺" else -1
                self.client.dbconn.execute("UPDATE talks SET time = time + ? WHERE message_id = ?", (increment, payload.message_id))
                self.client.dbconn.commit()

                await channel.send("<@{}> you have contributed {:.2f} Picocoin to make this talk {}.\n_You now have {:.2f} Picocoin._".format(
                    payload.user_id, row["price"], "longer" if increment > 0 else "shorter", total
                ))

                # Modify the embed
                cursor = self.client.dbconn.execute("SELECT * FROM talks WHERE message_id=?", (payload.message_id,))
                row = cursor.fetchone()
                embed.set_field_at(0, name="Duration:", value=format_time(row["time"]))
                await message.edit(embed=embed)
