import os
import logging
import pathlib
import sqlite3
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
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

# SQLite database initialization
db_path = pathlib.Path(__file__).parent.resolve() / "mercari.sqlite3"

def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                image TEXT NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
    logger.info("Database initialized")

init_db()

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.get("/items")
def get_items():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items.id, items.name, categories.name AS category, items.image FROM items INNER JOIN categories ON items.category_id = categories.id")
        items_data = cursor.fetchall()
    return {"items": items_data}

@app.post("/items")
async def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    try:
        logger.info(f"Receive item: {name}, Category: {category}")

        # Save category to the categories table (if not exists)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))

            # Retrieve category_id
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_id = cursor.fetchone()[0]

            # Save item information to the items table
            cursor.execute("INSERT INTO items (name, category_id, image) VALUES (?, ?, ?)", (name, category_id, image.filename))

        # Save the image with the original filename
        image_path = images / image.filename
        with open(image_path, "wb") as image_file:
            image_file.write(await image.read())

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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9000, reload=True)
