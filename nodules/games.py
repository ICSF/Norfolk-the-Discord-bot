from . import CoreNodule
from discord import Embed, Colour
from asyncio import sleep


class Nodule(CoreNodule):
    def __init__(self, client):
        self.channel_ids = [807944080193486858, 807944141119422496, 807944209894080543]
        super().__init__(client)

    async def on_message(self, message):
        if message.content.startswith('!playing'):
            try:
                _, table, *game = message.content.split(" ")
            except ValueError:
                embed = Embed(
                    description="**Syntax error.** The syntax is !playing <table number> <game>",
                    colour=Colour.red())
                embed.set_footer(text="For example !playing 1 Checkers")
                await message.channel.send(embed=embed)
                return

            try:
                table = int(table)
            except ValueError:
                embed = Embed(
                    description="The table number must be 1, 2, or 3.",
                    colour=Colour.red())
                embed.set_footer(text="For example !playing 1 Checkers")
                await message.channel.send(embed=embed)
                return

            if not 0 < table < 4:
                embed = Embed(
                    description="The table number must be 1, 2, or 3.",
                    colour=Colour.red())
                embed.set_footer(text="For example !playing 1 Checkers")
                await message.channel.send(embed=embed)
                return

            channel = self.client.get_channel(self.channel_ids[table-1])
            embed = Embed(
                description="Attempting to set the channel description...",
                colour=Colour.from_rgb(194, 124, 14))
            embed.set_footer(text="Note - this can only be done ~2 times per 10 minutes.")
            await message.channel.send(embed=embed)

            await channel.edit(name="Games table {} - {}".format(table, " ".join(game)))
            await sleep(30 * 60)
            await channel.edit(name="Games table {}".format(table))

