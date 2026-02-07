from indexing import Indexing
from shared.my_config import Config
from shared.data_loader import DataLoader
from shared.data_base import FaissDB

config = Config()
data_loader = DataLoader(config)
db = FaissDB(config)
indexing_service = Indexing(config, data_loader, db)

indexing_service.run_indexing()
