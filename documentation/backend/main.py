import os
import json
import shutil

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uvicorn
from tempfile import TemporaryDirectory

from PIL import Image


app = FastAPI(
    title="Documentation",
    description="API for OTD",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

POSTS_URL = 'https://jsonplaceholder.typicode.com/posts'
POSTS_PATH = 'posts.json'


@app.get('/posts')
async def get_posts():
    if not os.path.exists(POSTS_PATH):
        data = requests.get(POSTS_URL).json()
        with open(POSTS_PATH, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        with open(POSTS_PATH, 'r') as f:
            data = json.load(f)

    return data


# @app.get('/flip')
# async def flip_image(file: UploadFile = File(...)):
#     with TemporaryDirectory() as temp_dir:
#         temp_path = os.path.join(temp_dir, file.filename)

#         with open(temp_path, "wb") as f:
#                 shutil.copyfileobj(file.file, f)

#         image = Image.open(temp_path)
#         converted_img = image.transpose(Image.FLIP_TOP_BOTTOM)
#         converted_img.save(temp_path)

#         return FileResponse(
#                 temp_path,
#                 media_type=f"image/{image.format.lower() if image.format else 'png'}",
#                 filename=f"flipped_{file.filename}"
#             )
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)