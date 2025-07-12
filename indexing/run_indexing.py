import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from indexing import Indexing
from data_loader import DataLoader
from data_base import FaissDB

config = Config()
data_loader = DataLoader(config)
DB = FaissDB(config)
I = Indexing(config, data_loader, DB)


#I.run_indexing()
I.run_indexing('В 1965 году был основал самый большой волейбольный клуб в мире, назывался он "СуперМены". Это был первый шаг в развитии волейбола в СССР.')