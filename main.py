import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "data.json"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_data() -> dict:
    if DATA_PATH.exists():
        try:
            with DATA_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"progressions": [], "shapes": []}
    return {"progressions": [], "shapes": []}


def save_data(data: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Chord(BaseModel):
    root: str
    quality: str
    label: str


class ScaleInfo(BaseModel):
    key: str
    mode: str


class Progression(BaseModel):
    id: str = Field(default_factory=lambda: "")
    name: str
    scale: ScaleInfo
    chords: List[Chord]


class ProgressionCreate(BaseModel):
    name: str
    scale: ScaleInfo
    chords: List[Chord]


class ChordShape(BaseModel):
    id: str = Field(default_factory=lambda: "")
    chord: str
    position: Optional[str] = None
    diagram: dict


app = FastAPI(title="Chord Craft API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_store() -> dict:
    data = load_data()
    if "progressions" not in data:
        data["progressions"] = []
    if "shapes" not in data:
        data["shapes"] = []
    return data


@app.get("/api/progressions", response_model=List[Progression])
def list_progressions():
    data = get_store()
    return data["progressions"]


@app.post("/api/progressions", response_model=Progression, status_code=201)
def create_progression(payload: ProgressionCreate):
    data = get_store()
    new_id = f"prg-{len(data['progressions']) + 1:04d}"
    progression = Progression(
        id=new_id,
        name=payload.name,
        scale=payload.scale,
        chords=payload.chords,
    )
    data["progressions"].append(progression.dict())
    save_data(data)
    return progression


@app.put("/api/progressions/{progression_id}", response_model=Progression)
def update_progression(progression_id: str, payload: ProgressionCreate):
    data = get_store()
    for idx, existing in enumerate(data["progressions"]):
        if existing.get("id") == progression_id:
            updated = Progression(
                id=progression_id,
                name=payload.name,
                scale=payload.scale,
                chords=payload.chords,
            )
            data["progressions"][idx] = updated.dict()
            save_data(data)
            return updated
    raise HTTPException(status_code=404, detail="指定された進行が見つかりませんでした。")


@app.delete("/api/progressions/{progression_id}", status_code=204)
def delete_progression(progression_id: str):
    data = get_store()
    filtered = [p for p in data["progressions"] if p.get("id") != progression_id]
    if len(filtered) == len(data["progressions"]):
        raise HTTPException(status_code=404, detail="指定された進行が見つかりませんでした。")
    data["progressions"] = filtered
    save_data(data)


@app.get("/api/shapes", response_model=List[ChordShape])
def list_shapes():
    data = get_store()
    return data["shapes"]


@app.post("/api/shapes", response_model=ChordShape, status_code=201)
def create_shape(payload: ChordShape):
    data = get_store()
    new_id = f"shape-{len(data['shapes']) + 1:04d}"
    chord_shape = ChordShape(id=new_id, chord=payload.chord, position=payload.position, diagram=payload.diagram)
    data["shapes"].append(chord_shape.dict())
    save_data(data)
    return chord_shape


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=FileResponse)
def serve_index():
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="フロントエンドが見つかりませんでした。")
    return FileResponse(index_path)
