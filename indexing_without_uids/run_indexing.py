from config import Config
from indexing import Indexing
from data_loader import DataLoader

config = Config()
data_loader = DataLoader(config)
I = Indexing(config, data_loader=data_loader)
I.run_indexing()