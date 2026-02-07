from app.indexing import Indexing
from app.shared.my_config import Config
from app.shared.data_loader import DataLoader
from app.shared.data_base import FaissDB

config = Config('app/indexing/config.yaml')
data_loader = DataLoader(config)
db = FaissDB(config)
indexing_service = Indexing(config, data_loader, db)

indexing_service.run_indexing()
