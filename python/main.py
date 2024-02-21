import os
import logging
import pathlib
import json
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Path
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

def hash_image(image_data):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(image_data)
    return sha256_hash.hexdigest()

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.get("/items")
def get_items():
    items_data = read_items()
    return {"items": items_data}

@app.get("/items/{item_id}")
def get_item(item_id: int = Path(..., title="The ID of the item to get")):
    items_data = read_items()
    if 0 <= item_id < len(items_data):
        return items_data[item_id]
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.post("/items")
async def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    try:
        logger.info(f"Receive item: {name}, Category: {category}")

        # Read the image data and hash it
        image_data = await image.read()
        image_hash = hash_image(image_data)

        # Save the image with the hashed name
        image_filename = f"{image_hash}.jpg"
        image_path = images / image_filename
        with open(image_path, "wb") as image_file:
            image_file.write(image_data)

        # Save item information to items.json
        new_item = {"name": name, "category": category, "image": image_filename}
        items_data = read_items()
        items_data.append(new_item)
        write_items(items_data)

        return {"message": f"Item received: {name}, Category: {category}"}

    except Exception as e:
        logger.error(f"Error processing item: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
