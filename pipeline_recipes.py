import requests
from bs4 import BeautifulSoup
import json
import time
import os

# ---------- Step 1: Scrape all recipes ----------
def scrape_single_recipe(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled Recipe"

    image_div = soup.find("div", class_="recipe-meta__image")
    image_url = None
    if image_div:
        img_tag = image_div.find("img")
        if img_tag and img_tag.has_attr("src"):
            image_url = img_tag["src"]
            if image_url.startswith("./") or not image_url.startswith("http"):
                image_url = "https://www.essen-und-trinken.de" + image_url[1:]
                
    # ✅ Extract duration from known div structure
    duration_text = None
    cook_time_div = soup.find("div", class_="recipe-meta__item--cook-time")
    if cook_time_div:
        duration_span = cook_time_div.find("span", class_="u-typo--recipe-info-text")
        if duration_span:
            duration_text = duration_span.get_text(strip=True)


    amounts = soup.select("x-beautify-number.recipe-ingredients__amount")
    labels = soup.select("p.recipe-ingredients__label")
    ingredients = [f"{amt.get_text(strip=True)} {lbl.get_text(strip=True)}" for amt, lbl in zip(amounts, labels)]

    instructions = []
    nutrition = {}
    json_ld_tags = soup.find_all("script", type="application/ld+json")
    for tag in json_ld_tags:
        try:
            data = json.loads(tag.string)
            if isinstance(data, list):
                recipe_data = next((entry for entry in data if entry.get("@type") == "Recipe"), None)
            elif data.get("@type") == "Recipe":
                recipe_data = data
            else:
                continue

            if recipe_data:
                instructions = recipe_data.get("recipeInstructions", [])
                nutrition = recipe_data.get("nutrition", {})
                break
        except Exception:
            continue

    return {
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions,
        "nutrition": nutrition,
        "image_url": image_url,
        "source_link": url,
        "duration" : duration_text
    }


def scrape_all_recipes(url_file_path, output_path):
    with open(url_file_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    all_recipes = []
    for url in urls:
        print(f"🔄 Scraping: {url}")
        try:
            recipe = scrape_single_recipe(url)
            all_recipes.append(recipe)
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")
        time.sleep(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_recipes, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {len(all_recipes)} recipes saved to {output_path}")


# ---------- Step 2: Add summary_text to recipes ----------
def add_summary_text(recipe_file, output_path):
    with open(recipe_file, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    for recipe in recipes:
        ingredients = ", ".join(recipe.get("ingredients", []))
        nutrition = recipe.get("nutrition", {})

        calories = f"{nutrition.get('calories', 'N/A')} kcal"
        protein = f"{nutrition.get('proteinContent', 'N/A')}g protein"
        carbs = f"{nutrition.get('carbohydrateContent', 'N/A')}g carbs"
        fat = f"{nutrition.get('fatContent', 'N/A')}g fat"

        nutrition_text = ", ".join([calories, protein, carbs, fat])
        recipe["summary_text"] = f"Ingredients: {ingredients}. Nutrition: {nutrition_text}."

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)

    print(f"✅ summary_text added and saved to {output_path}")


# ---------- MAIN PIPELINE ----------
if __name__ == "__main__":
    print("🚀 Starting full recipe pipeline...\n")
    scrape_all_recipes("recipe_urls.txt", "all_recipes.json")
    add_summary_text("all_recipes.json", "recipes_with_summary.json")
    print("\n🎉 Pipeline complete! Ready for classification.")
