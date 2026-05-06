import sys
sys.path.append('../')  # add parent directory to path to import detecVisage
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from detecVisage import FacesDetects_from_bytes, FacesDraw


# create the FastAPI application
app = FastAPI()


# CORS — allows the browser to send requests to FastAPI
# without this, the browser blocks requests for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTE /add ──
# receives : firstName (text) + lastName (text) + photo (file)
# returns  : a confirmation message
@app.post("/add")
async def add_person(
    firstName: str = Form(...),
    lastName:  str = Form(...),
    photo:     UploadFile = File(...)
):
    contents = await photo.read()
    result, image = FacesDetects_from_bytes(contents)
    image_boxed = FacesDraw(image, result)

    # for now, just print what we received
    print(f"Received: {firstName} {lastName}, file: {photo.filename}")

    # respond to the website
    return {"message": f"{firstName} {lastName} added successfully"}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
