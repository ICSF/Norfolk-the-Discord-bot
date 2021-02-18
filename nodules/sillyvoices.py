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
            embed.set_author(name=message.author.nick,
                             url="https://discordapp.com/channels/@me/{}".format(message.author.id),
                             icon_url=message.author.avatar_url)
            embed.add_field(name="Price", value="{:.2f} <:picocoin:810623980222021652>".format(value))
            embed.add_field(name="Reply", value="to [this message]({}).".format(message.jump_url))

            m = await self.client.get_channel(811948177728864277).send(embed=embed)
            await m.add_reaction("❌")
            await message.channel.send("Your offer has been posted in <#811948177728864277>, <@{}>".format(message.author.id))

        if message.content.startswith('!request'):
            if message.channel.id != 810500717781188618:
                embed = Embed(title="Wrong channel",
                              description="Please post your voice requests in <#810500717781188618>.",
                              colour=Colour.red())
                await message.channel.send(embed=embed)
                return

            # Parse arguments
            try:
                _, value, *desc = message.content.split(" ")
                value = float(value)
            except ValueError:
                embed = Embed(
                    description="**Syntax error.** The syntax is `!request <bounty> <description>`",
                    colour=Colour.red())
                embed.set_footer(text="For example: !voice 3 I want someone to say 'I can do that, Dave'  in HAL 9000's voice.")
                await message.channel.send(embed=embed)
                return

            # Check if user has enough coin
            balance = self.client.picocoin.check(message.author.id)
            if balance < value:
                embed = Embed(
                    title="You don't have enough Picocoin to cover the bounty.",
                    description="You have set the bounty to {:.2f}. You currently have {:.2f} Picocoin.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                        value, balance
                    ),
                    colour=Colour.red())
                await message.channel.send(embed=embed)
                return

            # Post the embed
            embed = Embed(title="Voicing request", description=" ".join(desc), colour=Colour.purple())
            embed.set_author(name=message.author.nick,
                             url="https://discordapp.com/channels/@me/{}".format(message.author.id),
                             icon_url=message.author.avatar_url)
            embed.add_field(name="Bounty", value="{:.2f} <:picocoin:810623980222021652>".format(value))
            embed.add_field(name="Reply", value="to [this message]({}).".format(message.jump_url))

            m = await self.client.get_channel(811948177728864277).send(embed=embed)
            await m.add_reaction("❌")
            await message.channel.send("Your request has been posted in <#811948177728864277>, <@{}>".format(message.author.id))

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == 811948177728864277 and payload.emoji.name=="❌":
            message = await self.client.get_channel(811948177728864277).fetch_message(payload.message_id)
            embed = message.embeds[0]
            if payload.user_id == int(embed.author.url.split("/")[-1]):
                await message.delete()



