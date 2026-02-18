import json
from typing import Any, Dict, List, Optional, Union


class Snippet:
    def __init__(
        self,
        text: str,
        header: List[str],
        file: str,
        prev_text: Optional[str] = None,
        next_text: Optional[str] = None,
    ) -> None:
        self.text = text
        self.header = header
        self.file = file
        self.prev_text = prev_text
        self.next_text = next_text

    @staticmethod
    def custom_decoder(dct: Dict[str, Any]) -> Union["Snippet", Dict[str, Any]]:
        if '__type__' in dct and dct['__type__'] == 'Snippet':
            return Snippet(dct['text'], dct['header'], dct['file'], dct['previous paragraph'], dct['next paragraph'] )
        return dct

class SnippetEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
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
