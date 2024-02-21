import os
import logging
import pathlib
import json
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

items_file = pathlib.Path(__file__).parent.resolve() / "items.json"
items = []

def read_items():
    if items_file.is_file():
        with open(items_file, 'r') as file:
            return json.load(file).get("items", [])
    return []

def write_items(items_data):
    with open(items_file, 'w') as file:
        json.dump({"items": items_data}, file)

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.get("/items")
def get_items():
    items_data = read_items()
    return {"items": items_data}

@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...)):
    logger.info(f"Receive item: {name}")
    new_item = {"name": name, "category": category}
    items_data = read_items()
    items_data.append(new_item)
    write_items(items_data)
    return {"items": [new_item]}

@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name
    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")
    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"
    return FileResponse(image)
