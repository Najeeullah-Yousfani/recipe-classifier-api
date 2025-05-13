# 🧠 Recipe Classifier API

This project scrapes recipes from URLs, generates summary text, and uses a transformer (RoBERTa) to classify recipes based on user-selected medical impairments like PCOS, diabetes, gluten intolerance, etc.

Built with:
- FastAPI
- HuggingFace Transformers
- BeautifulSoup
- Zero-shot classification using `facebook/bart-large-mnli`

---

## ⚙️ Installation

```bash
# Clone the repo
git clone https://github.com/your-username/recipe-classifier-api.git
cd recipe-classifier-api


# Install dependencies
pip install -r requirements.txt

🚀 Run Full Pipeline (Scraping + Summary)
Make sure recipe_urls.txt contains one URL per line.
# Once the project is setup run the following command to scrap transform recipes
python pipeline_recipes.py

```

This will:

Scrape all recipes listed in recipe_urls.txt

Save them to all_recipes.json

Add summary text

Save the final data to recipes_with_summary.json

📦 Project Structure
├── recipe_urls.txt              # List of URLs to scrape
├── all_recipes.json             # Raw scraped recipes
├── recipes_with_summary.json    # Final processed file with summary_text
├── pipeline_recipes.py          # End-to-end scraper + summary generator
├── recipe_cache_layer.py        # FastAPI + RoBERTa + in-memory cache
├── requirements.txt             # All dependencies
└── README.md

✅ Example Conditions to Test
pcos

diabetes

gluten intolerance

high blood pressure

lactose intolerance

vegan

keto