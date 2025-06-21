from config import Config

from indexing import Indexing

config = Config()
I = Indexing(config)
I.run_indexing()