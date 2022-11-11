from typing import List

from .generic import JsonData, ResultData


"""
Structure of data:
SaucenaoResponse {
    "header": SaucenaoResponseHeader {
        "index": SaucenaoResponseIndex {
            SaucenaoResponseIndexData.id: SaucenaoResponseIndexData
        }
    }
    "results": [
        SaucenaoResult {
            "header": SaucenaoResultHeader,
            "data": JsonData,
        }
    ]
}
SaucenaoResponse
+-- SaucenaoHeader
|   +-- SaucenaoResponseIndex
|       +-- SaucenaoResponseIndexData
+-- results
    +-- SaucenaoResult
        +-- JsonData
        +-- SaucenaoResultHeader
"""


class SaucenaoResponseIndexData(JsonData):
    def __init__(self,
                 status: int,
                 index_id: int,
                 results: int):
        self.status = status
        self.index_id = index_id
        self.results = results

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(
            json_dict['status'],
            json_dict['id'],
            json_dict['results']
        )


class SaucenaoResponseIndex(JsonData):
    def __init__(self, indexes: List[SaucenaoResponseIndexData]):
        self.indexes = indexes

    @classmethod
    def from_json(cls, json_list: List):
        return cls(
            [SaucenaoResponseIndexData
             .from_json(index) for index in json_list]
        )


class SaucenaoResultHeader(JsonData):
    """Contains information about the type of result"""

    def __init__(self,
                 similarity: int,
                 index_id: int):
        self.similarity = similarity
        self.index_id = index_id

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict['similarity'],
                   json_dict['index_id'])


class SaucenaoResult(JsonData):
    """Represents a result inside the 'results' array"""

    def __init__(self,
                 header: SaucenaoResultHeader,
                 data: ResultData):
        self.header = header
        self.data = data


class SaucenaoResponseHeader(JsonData):
    """Top level header in a Saucenao API response"""

    def __init__(self,
                 user_id: int,
                 short_limit: int,
                 long_limit: int,
                 short_remaining: int,
                 long_remaining: int,
                 status: int,
                 search_depth: int,
                 minimum_similarity: int,
                 results_returned: int,
                 index: SaucenaoResultHeader):
        self.user_id = user_id
        self.short_limit = short_limit
        self.long_limit = long_limit
        self.short_remaining = short_remaining
        self.long_remaining = long_remaining
        self.status = status
        self.search_depth = search_depth
        self.minimum_similarity = minimum_similarity
        self.results_returned = results_returned
        self.index = index

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict['user_id'],
                   json_dict['short_limit'],
                   json_dict['long_limit'],
                   json_dict['short_remaining'],
                   json_dict['long_remaining'],
                   json_dict['status'],
                   json_dict['search_depth'],
                   json_dict['minimum_similarity'],
                   json_dict['results_returned'],
                   json_dict['index'])


class SaucenaoResponse(JsonData):
    """Full response of the Saucenao API"""

    def __init__(self,
                 header: SaucenaoResponseHeader,
                 results: List[SaucenaoResult]):
        self.header = header
        self.results = results

    @classmethod
    def from_json(cls, json_dict):
        header = SaucenaoResponseHeader.from_json(json_dict['header'])
        results = [result
                   for result in cls.from_json(
                       json_dict['results'])]

        return cls(header, results)
