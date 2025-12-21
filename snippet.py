import json


class Snippet:
    def __init__(self, text, header, file, prev_text = None, next_text = None):
        self.text = text
        self.header = header
        self.file = file
        self.prev_text = prev_text
        self.next_text = next_text

    def custom_decoder(dct):
        if '__type__' in dct and dct['__type__'] == 'Snippet':
            return Snippet(dct['text'], dct['header'], dct['file'], dct['previous paragraph'], dct['next paragraph'] )
        return dct

class SnippetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Snippet):
            return{
                '__type__': 'Snippet',
                'text': obj.text,
                'header': obj.header,
                'file': obj.file,
                'previous paragraph': obj.prev_text,
                'next paragraph': obj.next_text,
            }
        return super().default(obj)