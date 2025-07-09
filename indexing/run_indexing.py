from config import Config
from indexing import Indexing
from data_loader import DataLoader
from data_base import FaissDB

config = Config()
data_loader = DataLoader(config)
DB = FaissDB(config)
I = Indexing(config, data_loader)


I.run_indexing()