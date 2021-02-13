from . import CoreNodule


class Nodule(CoreNodule):
    async def on_message(self, message):
        if message.content.startswith('!send') and message.author.guild_permissions.administrator:
            s = message.content.split(" ")
            channel = self.client.get_channel(int(s[1][2:-1]))
            contents = " ".join(s[2:])
            await channel.send(contents)

        if message.content.startswith('!edit') and message.author.guild_permissions.administrator:
            s = message.content.split(" ")
            channel = self.client.get_channel(int(s[1][2:-1]))
            message = await channel.fetch_message(int(s[2]))
            contents = " ".join(s[3:])
            await message.edit(content=contents)
