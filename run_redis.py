import subprocess
import redis 


import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
from shared.logs import setup_logging


logger = setup_logging('logs', 'Redis')

dump_dir = './data/'
dump_file_name = 'rubq_dump.rdb'
port = "6379"

os.makedirs(dump_dir, exist_ok=True)


redis_process = subprocess.Popen([
    'redis-server',
    '--port', str(port),
    '--dir', dump_dir,
    '--dbfilename', dump_file_name,
    '--save', '60', '1'
])

logger.info('Redis server started')
logger.info(f'Dump file saved to: {os.path.join(dump_dir, "rubq_dump.rdb")}')