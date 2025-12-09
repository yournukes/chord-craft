import json
import os
import uuid
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


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class Chord(BaseModel):
    root: str
    quality: str
    label: str
    bass: Optional[str] = None


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


class Diagram(BaseModel):
    startFret: int = Field(default=1, ge=1)
    frets: List[int] = Field(..., min_items=6, max_items=6)


class ChordShapePayload(BaseModel):
    chord: str
    position: Optional[str] = None
    diagram: Diagram


class ChordShape(ChordShapePayload):
    id: str = Field(default_factory=lambda: "")


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
    changed = False

    for key in ["progressions", "shapes"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
            changed = True

    changed = normalize_ids(data, "progressions", "prg") or changed
    changed = normalize_ids(data, "shapes", "shape", normalizer=normalize_shape_entry) or changed

    if changed:
        save_data(data)

    return data


def normalize_shape_entry(entry: dict) -> bool:
    changed = False
    chord = str(entry.get("chord", "")).strip()
    if not chord:
        chord = "無題のコード"
    if entry.get("chord") != chord:
        entry["chord"] = chord
        changed = True
    return changed


def normalize_ids(data: dict, key: str, prefix: str, normalizer=None) -> bool:
    if key not in data or not isinstance(data[key], list):
        return False

    seen_ids = set()
    changed = False

    for item in data[key]:
        if not isinstance(item, dict):
            continue

        item_id = item.get("id")
        if not item_id or item_id in seen_ids:
            item["id"] = generate_id(prefix)
            changed = True
        seen_ids.add(item["id"])

        if normalizer and normalizer(item):
            changed = True

    return changed


@app.get("/api/progressions", response_model=List[Progression])
def list_progressions():
    data = get_store()
    return data["progressions"]


@app.post("/api/progressions", response_model=Progression, status_code=201)
def create_progression(payload: ProgressionCreate):
    data = get_store()
    progression = Progression(
        id=generate_id("prg"),
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
def create_shape(payload: ChordShapePayload):
    data = get_store()
    chord_shape = ChordShape(
        id=generate_id("shape"),
        chord=payload.chord.strip() or "無題のコード",
        position=payload.position,
        diagram=payload.diagram,
    )
    data["shapes"].append(chord_shape.dict())
    save_data(data)
    return chord_shape


@app.put("/api/shapes/{shape_id}", response_model=ChordShape)
def update_shape(shape_id: str, payload: ChordShapePayload):
    data = get_store()
    for idx, existing in enumerate(data["shapes"]):
        if existing.get("id") == shape_id:
            updated = ChordShape(
                id=shape_id,
                chord=payload.chord.strip() or "無題のコード",
                position=payload.position,
                diagram=payload.diagram,
            )
            data["shapes"][idx] = updated.dict()
            save_data(data)
            return updated
    raise HTTPException(status_code=404, detail="指定されたフォームが見つかりませんでした。")


@app.delete("/api/shapes/{shape_id}", status_code=204)
def delete_shape(shape_id: str):
    data = get_store()
    filtered = [s for s in data["shapes"] if s.get("id") != shape_id]
    if len(filtered) == len(data["shapes"]):
        raise HTTPException(status_code=404, detail="指定されたフォームが見つかりませんでした。")
    data["shapes"] = filtered
    save_data(data)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=FileResponse)
def serve_index():
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="フロントエンドが見つかりませんでした。")
    return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
