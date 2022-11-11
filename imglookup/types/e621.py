from typing import List

from .generic import ResultData


class E621Result(ResultData):
    keys = ["ext_urls", "e621_id", "source"]

    def __init__(self,
                 ext_urls: List[str],
                 e621_id: int,
                 source: str):
        self.ext_urls = ext_urls
        self.e621_id = e621_id
        self.source = source
