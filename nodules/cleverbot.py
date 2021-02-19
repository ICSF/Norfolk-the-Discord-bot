from . import CoreNodule
from discord import Embed, Colour
import random

class Nodule(CoreNodule):
    def __init__(self, client):
        self.symbols = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "questions" (
                                 "id" INTEGER UNIQUE,
                                 "message_id" INTEGER,
                                 "vote_id" INTEGER,
                                 "question_text" TEXT,
                                 "price" NUMERIC,
                                 "bot_answer" TEXT,
                                 "rng" NUMERIC,
                                 PRIMARY KEY("id" AUTOINCREMENT)
                                 );''')
        client.dbconn.execute('''CREATE TABLE IF NOT EXISTS "answers" (
                                 "id" INTEGER UNIQUE,
                                 "question" INTEGER,
                                 "user_id" INTEGER,
                                 "channel_id" INTEGER,
                                 "answer" TEXT,
                                 "rng" NUMERIC,
                                 PRIMARY KEY("id" AUTOINCREMENT),
                                 FOREIGN KEY("question") REFERENCES "questions"("id")
                                 );''')
        super().__init__(client)

    async def on_message(self, message):
        if message.content.startswith('!question') and message.author.guild_permissions.administrator:
            # Parse arguments
            try:
                _, price, *text = message.content.split(" ")
                price = float(price)
                text = " ".join(text)
                question, bot_answer = text.split("\n")
            except ValueError:
                embed = Embed(
                    description="**Syntax error.** The syntax is `!question <price> <question>\\n<answer>`",
                    colour=Colour.red())
                await message.channel.send(embed=embed)
                return

            # Generate the embed
            embed = Embed(title="Turing test question", description="The question is ```{}```\nTo answer, click the :white_check_mark: reaction and check for direct messages.".format(question), colour=Colour.blue())
            embed.add_field(name="Price:", value="**{:.2f}**<:picocoin:810623980222021652>".format(price))
            embed.add_field(name="Answers:", value="1/1")
            embed.set_footer(text="Your entry payment goes in a pool. The pool is then distrbuted according to the number of votes your answer gets.")
            m = await self.client.get_channel(810500753566203914).send(embed=embed)

            # Insert into the database
            self.client.dbconn.execute("INSERT INTO questions (message_id, question_text, price, bot_answer, rng) VALUES (?, ?, ?, ?, ?)",
                                       (m.id, question, price, bot_answer, random.random()))
            cursor = self.client.dbconn.execute("SELECT id FROM questions WHERE message_id=?", (m.id,))
            row = cursor.fetchone()
            self.client.dbconn.execute("INSERT INTO answers (question, answer, rng) VALUES (?, ?, ?)",
                                       (row["id"], bot_answer, random.random()))
            self.client.dbconn.commit()

            # Add reactions
            await m.add_reaction("✅")

        if message.content.startswith('!vote') and message.author.guild_permissions.administrator and message.channel.id==810500753566203914:
            price = float(message.content[6:])

            # Delete users who have not sent in answers
            self.client.dbconn.execute("DELETE FROM answers WHERE answer IS NULL AND user_id")
            self.client.dbconn.commit()

            text = ""
            cursor = self.client.dbconn.execute("SELECT qs.question_text, answer FROM answers INNER JOIN (SELECT * FROM questions ORDER BY id DESC LIMIT 1) as qs ON answers.question=qs.id ORDER BY answers.rng")
            for i, row in enumerate(cursor):
                text += "{}: {}\n".format(self.symbols[i], row["answer"])
            embed = Embed(title="Turing test voting!",
                          description="The question was ```{}```\nThe answers are:\n\n{}".format(row["question_text"], text),
                          colour=Colour.blurple())
            embed.add_field(name="Price:", value="**{:.2f}**<:picocoin:810623980222021652>".format(price))
            embed.set_footer(text="To vote, click a reaction below. Votes cost the amount of Picocoin stated above, the people who guess right get the Picocoin of those who guessed wrong.")
            m = await self.client.get_channel(810500753566203914).send(embed=embed)
            for j in range(i+1):
                await m.add_reaction(self.symbols[j])

            # Set the vote message id in the database
            self.client.dbconn.execute("UPDATE questions SET vote_id=? ORDER BY id DESC LIMIT 1", (m.id,))
            self.client.dbconn.commit()


        if message.guild is None:
            cursor = self.client.dbconn.execute("SELECT * FROM answers INNER JOIN (SELECT * FROM questions ORDER BY id DESC LIMIT 1) as qs ON answers.question=qs.id WHERE user_id=? AND answer IS NULL",
                                                (message.author.id,))
            row = cursor.fetchone()
            if row:
                # Check if balance still high enough
                total = self.client.picocoin.check(message.author.id)
                if total < row["price"]:
                    embed = Embed(
                        description="**You don't have enough Picocoin to participate.**\nYou have {:.2f}, but you need {:.2f}.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                            total, row["price"]
                        ),
                        colour=Colour.red())
                    await message.channel.send(embed=embed)
                    return
                total = self.client.picocoin.take(message.author.id, row["price"])

                # Update the database
                self.client.dbconn.execute("UPDATE answers SET answer=? WHERE user_id=? AND question=?",
                                           (message.content, row["user_id"], row["question"]))
                self.client.dbconn.commit()

                # Send acknowledging message
                embed = Embed(
                    description="Your answer to```{}```\n has been recorded.\n\n You have been charged {:.2f} Picocoin, and now have {:.2f}.".format(
                        row["question_text"], row["price"], total
                    ),
                    colour=Colour.blue())
                await message.channel.send(embed=embed)

                # Update the question embed
                q_message = await self.client.picoguild.get_channel(810500753566203914).fetch_message(row["message_id"])
                embed = q_message.embeds[0]
                cursor = self.client.dbconn.execute(
                    "SELECT COUNT(answers.answer) AS answered, COUNT(answers.id) AS questioned FROM answers INNER JOIN questions on answers.question=questions.id WHERE message_id=?",
                    (row["message_id"],))
                row = cursor.fetchone()
                embed.set_field_at(1, name="Answers:", value="{}/{}".format(row["answered"], row["questioned"]))
                await q_message.edit(embed=embed)

                return

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == 810500753566203914 and payload.emoji.name=="✅":
            channel = self.client.get_channel(810500753566203914)
            cursor = self.client.dbconn.execute("SELECT * FROM questions WHERE message_id=? AND vote_id IS NULL", (payload.message_id,))
            row = cursor.fetchone()
            if row:
                # Check if user has enough coin
                total = self.client.picocoin.check(payload.user_id)
                if total < row["price"]:
                    embed = Embed(
                        description="**You don't have enough Picocoin to participate.**\nYou have {:.2f}, but you need {:.2f}.\n_Donate now at https://www.union.ic.ac.uk/scc/icsf/donate/_".format(
                            total, row["price"]
                        ),
                        colour=Colour.red())
                    await payload.member.send(embed=embed)
                    return

                # Check if user already answered this question
                cursor = self.client.dbconn.execute("SELECT * FROM answers INNER JOIN questions on answers.question=questions.id WHERE message_id=? AND user_id=?",
                                                    (payload.message_id, payload.user_id))
                if cursor.fetchone():
                    embed = Embed(
                        description="You are alrady participating in this round of the Turing test.",
                        colour=Colour.red())
                    await payload.member.send(embed=embed)
                    return

                # Fetch the qeustion message and its embed
                q_message = await channel.fetch_message(payload.message_id)
                embed = q_message.embeds[0]

                u_embed = Embed(title="Turing test question",
                                description="The question is ```{}```\nPost your answer directly in this chat.".format(
                                row["question_text"]), colour=Colour.blue())
                u_message = await payload.member.send(embed=u_embed)

                # Add a placeholder row to the db
                self.client.dbconn.execute(
                    "INSERT INTO answers (question, user_id, channel_id, rng) VALUES (?, ?, ?, ?)",
                    (row["id"], payload.user_id, u_message.channel.id, random.random()))
                self.client.dbconn.commit()

                cursor = self.client.dbconn.execute("SELECT COUNT(answers.answer) AS answered, COUNT(answers.id) AS questioned FROM answers INNER JOIN questions on answers.question=questions.id WHERE message_id=?",
                                                    (payload.message_id,))
                row = cursor.fetchone()
                embed.set_field_at(1, name="Answers:", value="{}/{}".format(row["answered"], row["questioned"]))
                await q_message.edit(embed=embed)