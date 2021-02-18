from . import CoreNodule
from discord import Embed, Colour


def format_time(minutes):
    return "{:d}:{:02d}".format(int(minutes), int((minutes % 1)*60))

class Nodule(CoreNodule):
    def __init__(self, client):
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "fish" (
                                 "id" INTEGER UNIQUE,
                                 "message_id" NUMERIC,
                                 "duration" NUMERIC,
                                 "description" TEXT,
                                 "attack" NUMERIC,
                                 "defence" NUMERIC,
                                 "price" NUMERIC,
                                 "message_id" INTEGER,
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
            embed.add_field(name="Price:", value="{:.2f} <:picocoin:810623980222021652> per {}".format(price, format_time(increment)))

            # Add reactions
            m = await message.channel.send(embed=embed)
            await m.add_reaction("🔺")
            await m.add_reaction("🔻")


    async def on_raw_reaction_add(self, payload):
        pass
        # if payload.channel_id == 811948177728864277 and payload.emoji.name=="❌":
        #     message = await self.client.get_channel(811948177728864277).fetch_message(payload.message_id)
        #     embed = message.embeds[0]
        #     if payload.user_id == int(embed.author.url.split("/")[-1]):
        #         await message.delete()



