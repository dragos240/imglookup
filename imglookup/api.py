from abc import ABC, abstractclassmethod
from typing import Iterable

from dotenv import load_dotenv


class ApiError(Exception):
    """For SauceNao API/Index issues"""
    pass


class DBType:
    GELBOORU = 25
    E621 = 29


class Api(ABC):
    def __init__(self):
        load_dotenv()

    @abstractclassmethod
    def get_results(self):
        """Returns the results"""
        raise NotImplemented()

    @abstractclassmethod
    def crawl(self, paths: Iterable[str]):
        """Crawls for paths"""
        raise NotImplemented()
