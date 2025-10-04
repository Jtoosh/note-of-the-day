import json


class Snippet:
    def __init__(self, text, header, file):
        self.text = text
        self.header = header
        self.file = file
        self.last_seen = None

    def custom_decoder(dct):
        if '__type__' in dct and dct['__type__'] == 'Snippet':
            return Snippet(dct['text'], dct['header'], dct['file'], dct['last_seen'] )
        return dct

class SnippetEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__