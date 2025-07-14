import sys
import os
import shutil

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from tempfile import TemporaryDirectory

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
from logs import setup_logging
from indexing import Indexing
from my_config import Config
from data_loader import DataLoader
from data_base import FaissDB, ChromaDB


config = Config()
logger = setup_logging(config.logs_dir, 'CommunicateAPI')
data_loader = DataLoader(config)
data_base = FaissDB(config)
I = Indexing(config, data_loader, data_base)

app = FastAPI(title='Communicate API',
              description='API for create, load and update vector DB')

@app.post('/upload-files')
async def upload_file(file: UploadFile=File(...)):
    with TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        logger.info(f"File saved to temp directory: {temp_path}")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Start indexing...")
            I.run_indexing(data=temp_path)
            logger.info("End indexing!")
            return {"message": "File processed and indexed successfully."}
        except Exception as e:
            return {"error": str(e)}

