from rag_system.indexing import Indexing
from rag_system.shared.my_config import Config
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.data_base import FaissDB

config = Config('rag_system/indexing/config.yaml')
data_loader = DataLoader(config)
db = FaissDB(config)
indexing_service = Indexing(config, data_loader, db)

indexing_service.run_indexing()
