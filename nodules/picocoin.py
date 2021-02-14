from . import CoreNodule
from discord import Embed, Colour
from discord.ext.tasks import loop
from aiohttp import ClientSession

app_key = "app_key"
url = "https://api.staging.justgiving.com/{}/v1/".format(app_key)
fundraiser = "save-endors-forests"

class Nodule(CoreNodule):
    def __init__(self, client):

        # client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "treasure" (
        #                          "id" INTEGER UNIQUE,
        #                          "name" TEXT,
        #                          "value" INTEGER,
        #                          PRIMARY KEY("id" AUTOINCREMENT)
        #                          );''')
        self.get_donations.start()
        super().__init__(client)

    async def on_message(self, message):
        pass

    async def on_raw_reaction_add(self, payload):
        pass

    @loop(seconds=10)
    async def get_donations(self):
        await self.client.get_channel(808080178965381171).send("message")
        async with ClientSession() as session:
            async with session.get(url+'fundraising/pages/{}/donations'.format(fundraiser), headers={"Accept": "application/json"}) as r:
                await self.client.get_channel(808080178965381171).send(r.status)
                if r.status == 200:
                    js = await r.json()
                    await self.client.get_channel(808080178965381171).send(js["donations"][0]["amount"])
