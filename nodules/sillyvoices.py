from . import CoreNodule
from discord import Embed, Colour


class Nodule(CoreNodule):
    def __init__(self, client):
        super().__init__(client)

    async def on_message(self, message):
        if message.content.startswith('!voice'):
            if message.channel.id != 810500717781188618:
                embed = Embed(title="Wrong channel",
                              description="Please post your voice offers in <#810500717781188618>.",
                              colour=Colour.red())
                await message.channel.send(embed=embed)
                return

            # Parse arguments
            try:
                _, value, *desc = message.content.split(" ")
                value = float(value)
            except ValueError:
                embed = Embed(
                    description="**Syntax error.** The syntax is `!voice <price> <description>`",
                    colour=Colour.red())
                embed.set_footer(text="For example: !voice 3 I will say your prompt in HAL 9000's voice.")
                await message.channel.send(embed=embed)
                return

            # Post the embed
            embed = Embed(title="Voicing offer", description=" ".join(desc), colour=Colour.orange())
            embed.set_author(name=message.author.nick, url=message.jump_url, icon_url=message.author.avatar_url)
            embed.add_field(name="Price", value="{:.2f} <:picocoin:810623980222021652>".format(value))
            embed.add_field(name="Reply", value="to [this message]({}).".format(message.jump_url))

            await self.client.get_channel(811948177728864277).send(embed=embed)
            await message.channel.send("Your offer has been posted in <#811948177728864277>, <@{}>".format(message.author.id))



