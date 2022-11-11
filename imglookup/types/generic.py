from abc import ABC
import json
from typing import Any, List


class JsonData(ABC):
    """Abstract data class"""

    def __str__(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        return self.__str__()

    @classmethod
    def from_json(cls, json_dict: Any):
        return cls()


class ResultData(JsonData):
    keys: List[str] = []

    def __getattr__(self, name: str):
        if name in self.keys:
            return self.__getattribute__(name)
        else:
            raise AttributeError()
