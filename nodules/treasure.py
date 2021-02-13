from . import CoreNodule


class Nodule(CoreNodule):
    def __init__(self, client):
        self.roles = {
            "🟥": 810245249711603782,
            "🟩": 810245345094664243,
            "🟦": 810245370742439946
        }
        super().__init__(client)

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == 807945982556897301 and payload.message_id == 810241676937003018:
            role_ids = [x.id for x in payload.member.roles]
            if (not any([x in role_ids for x in self.roles.values()])) and payload.emoji.name in self.roles.keys():
                role = self.client.picoguild.get_role(self.roles[payload.emoji.name])
                await payload.member.add_roles(role)


