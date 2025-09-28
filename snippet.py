class Snippet:
    def __init__(self, text, header, file):
        self.text = text
        self.header = header
        self.file = file
        self.last_seen = None