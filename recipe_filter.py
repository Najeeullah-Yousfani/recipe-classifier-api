from fastapi import FastAPI, Query
from typing import List, Dict, Any
import json
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware
from tqdm import tqdm
import hashlib

# ------------------ CONFIG ------------------
RECIPE_FILE = "recipes_with_summary.json"
MODEL_NAME = "facebook/bart-large-mnli"
SCORE_THRESHOLD = 0.5

# ------------------ LOAD DATA ------------------
with open(RECIPE_FILE, "r", encoding="utf-8") as f:
    all_recipes = json.load(f)

# ------------------ LOAD MODEL ------------------
classifier = pipeline("zero-shot-classification", model=MODEL_NAME)

# ------------------ INIT APP & CACHE ------------------
app = FastAPI()
cache: Dict[str, Dict[str, Any]] = {}  # key: hash, value: classification result

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ UTILS ------------------
def hash_key(text: str, conditions: List[str]) -> str:
    key = text + ";" + ",".join(sorted(conditions))
    return hashlib.md5(key.encode("utf-8")).hexdigest()

def classify_recipe(text: str, conditions: List[str]) -> dict:
    cache_key = hash_key(text, conditions)
    if cache_key in cache:
        return cache[cache_key]

    if not conditions:
        result = {"label": "Not suitable", "score": 0.0, "combined_condition": ""}
    else:
        if len(conditions) == 1:
            combined = conditions[0]
        else:
            combined = ", ".join(conditions[:-1]) + f", and {conditions[-1]}"

        labels = [
            f"This recipe is suitable for someone with {combined}",
            f"This recipe is not suitable for someone with {combined}"
        ]

        result_raw = classifier(text, labels)
        result = {
            "label": result_raw["labels"][0],
            "score": result_raw["scores"][0],
            "combined_condition": combined
        }

    cache[cache_key] = result
    return result

# ------------------ API ROUTE ------------------
@app.get("/get_recipes", response_model=List[Dict[str, Any]])
def get_recipes(conditions: List[str] = Query(..., description="List of medical impairments")):
    matching = []
    for recipe in tqdm(all_recipes, desc="Classifying recipes"):
        text = recipe.get("summary_text", "")
        if not text:
            continue
        result = classify_recipe(text, conditions)

        if result["label"].lower().startswith("this recipe is suitable") and result["score"] >= SCORE_THRESHOLD:
            recipe["classification_score"] = result["score"]
            recipe["classification_label"] = result["label"]
            matching.append(recipe)

    matching.sort(key=lambda r: r["classification_score"], reverse=True)
    return matching
