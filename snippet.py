import json


class Snippet:
    def __init__(self, text, header, file):
        self.text = text
        self.header = header
        self.file = file
        self.last_seen = None

    def custom_decoder(dct):
        if '__type__' in dct and dct['__type__'] == 'Snippet':
            return Snippet(dct['text'], dct['header'], dct['file'] )
        return dct

class SnippetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Snippet):
            return{
                '__type__': 'Snippet',
                'text': obj.text,
                'header': obj.header,
                'file': obj.file,
                'last_seen': obj.last_seen
            }
        return super().default(obj)