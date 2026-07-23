from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class Snippet:
    text: str
    header: List[str]
    file: str
    prev_text: Optional[str] = None
    next_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "__type__": "Snippet",
            "text": self.text,
            "header": self.header,
            "file": self.file,
            "prev_text": self.prev_text,
            "next_text": self.next_text,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> Union["Snippet", Dict[str, Any]]:
        if dct.get("__type__") != "Snippet":
            return dct
        return cls(
            text=dct["text"],
            header=dct["header"],
            file=dct["file"],
            prev_text=dct.get("prev_text") or dct.get("previous paragraph"),
            next_text=dct.get("next_text") or dct.get("next paragraph"),
        )
