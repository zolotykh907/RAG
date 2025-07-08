from config import Config

from indexing_without_uid import Indexing

config = Config()
I = Indexing(config)
I.run_indexing()