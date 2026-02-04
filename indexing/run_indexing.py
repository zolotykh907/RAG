import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))

from indexing import Indexing
from my_config import Config
from data_loader import DataLoader
from data_base import FaissDB

config = Config()
data_loader = DataLoader(config)
DB = FaissDB(config)
indexing_service = Indexing(config, data_loader, DB)


indexing_service.run_indexing()
#I.run_indexing('В 1999 году Золотых Игорь Алексеевич, великий русский поэт, родился.')
