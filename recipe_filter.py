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
SCORE_THRESHOLD = 0.0

# ------------------ LOAD DATA ------------------
with open(RECIPE_FILE, "r", encoding="utf-8") as f:
    all_recipes = json.load(f)

# ------------------ LOAD MODEL ------------------
classifier = pipeline("zero-shot-classification", model=MODEL_NAME)

# ------------------ INIT APP & CACHE ------------------
app = FastAPI()
classification_cache: Dict[str, Dict[str, Any]] = {}
diet_cache: Dict[str, str] = {}

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
    if cache_key in classification_cache:
        return classification_cache[cache_key]

    if not conditions:
        result = {"label": "Not suitable", "score": 0.0, "combined_condition": ""}
    else:
        suitable_count = 0
        total_score = 0.0
        for condition in conditions:
            labels = [
                f"This recipe is suitable for someone with {condition}",
                f"This recipe is not suitable for someone with {condition}"
            ]
            result_raw = classifier(text, labels)
            label = result_raw["labels"][0]
            score = result_raw["scores"][0]
            if label.startswith("This recipe is suitable"):
                suitable_count += 1
                total_score += score

        if suitable_count == len(conditions):
            result = {
                "label": "This recipe is suitable",
                "score": total_score / len(conditions),
                "combined_condition": ", ".join(conditions)
            }
        else:
            result = {
                "label": "Not suitable",
                "score": 0.0,
                "combined_condition": ", ".join(conditions)
            }

    classification_cache[cache_key] = result
    return result

def classify_diet(text: str, diet: str) -> bool:
    # Supported diets: "vegetarian", "non-vegetarian"
    if not diet:
        return True  # No filtering
    
    labels = [
        f"This recipe is vegetarian",
        f"This recipe is non-vegetarian"
    ]
    result = classifier(text, labels)
    predicted_label = result["labels"][0].lower()

    if diet == "vegetarian" and "vegetarian" in predicted_label:
        return True
    if diet == "non-vegetarian" and "non-vegetarian" in predicted_label:
        return True
    return False


# ------------------ API ROUTE ------------------
@app.get("/get_recipes", response_model=List[Dict[str, Any]])
def get_recipes(
    conditions: List[str] = Query(..., description="List of medical impairments"),
    diet: str = Query(None, description="Diet preference: vegetarian, non-vegetarian")
):
    matching = []
    for recipe in tqdm(all_recipes, desc="Classifying recipes"):
        if (
            not recipe.get("title") or
            recipe["title"].strip().lower() == "die gewünschte seite ist leider nicht vorhanden" or
            not recipe.get("ingredients") or
            not recipe.get("instructions") or
            not recipe.get("nutrition")
        ):
            continue

        text = recipe.get("summary_text", "")
        if not text:
            continue

        result = classify_recipe(text, conditions)

        if result["label"].lower().startswith("this recipe is suitable") and result["score"] >= SCORE_THRESHOLD:
            # Check diet suitability here
            if classify_diet(text, diet):
                recipe["classification_score"] = result["score"]
                recipe["classification_label"] = result["label"]
                matching.append(recipe)

    matching.sort(key=lambda r: r["classification_score"], reverse=True)
    return matching
    # return JSONResponse(content={
    #     "count": len(matching),
    #     "recipes": matching
    # }
