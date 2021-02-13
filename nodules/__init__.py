class Nodule:
    def __init__(self, client):
        self.client = client

    def on_message(self, message):
        pass

    def on_raw_reaction_add(self, payload):
        pass