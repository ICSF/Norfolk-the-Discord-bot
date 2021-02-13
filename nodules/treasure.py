from . import CoreNodule


class Nodule(CoreNodule):
    async def on_raw_reaction_add(self, payload):
        print("reaction!")
