from . import CoreNodule
from discord import Embed, Colour


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
        if message.content.startswith('!fishmarket') and message.author.guild_permissions.administrator:
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

        if message.content.startswith('!slap'):
            self.ensure_fish(message.author.id)

    def ensure_fish(self, user_id):
        self.client.dbconn.execute("INSERT OR IGNORE INTO hp (user_id) VALUES (?)", (user_id,))
        self.client.dbconn.commit()
        cursor = self.client.dbconn.execute(
            "SELECT * FROM fish_ownership INNER JOIN hp on fish_ownership.owner=hp.user_id WHERE hp.user_id=?",
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
            row = cursor.fetchone()
            if row:
                cursor = self.client.dbconn.execute("SELECT id FROM hp WHERE user_id=?", (payload.user_id,))
                owner_id = cursor.fetchone()["id"]
                self.client.dbconn.execute("INSERT INTO fish_ownership (owner, fish) VALUES (?, ?)", (owner_id, row["id"]))
                self.client.dbconn.commit()
