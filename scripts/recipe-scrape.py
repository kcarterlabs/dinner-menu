import requests
from bs4 import BeautifulSoup

# Load your bookmarks.html file
with open('bookmarks.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

# Extract links containing recipe keywords
recipe_links = ["https://www.loveandlemons.com/minestrone-soup/","https://www.thewholesomedish.com/the-best-classic-shepherds-pie/#recipe","https://iowagirleats.com/gluten-free-breakfast-casserole/"]
for a in soup.find_all('a'):
    text = a.get_text().lower()
    href = a.get('href')
    if 'recipe' in text or 'food' in text:
        recipe_links.append(href)

print(f"Found {len(recipe_links)} possible recipe links:")
for link in recipe_links:
    print(link)


def scrape_recipe(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        title = soup.title.string.strip() if soup.title else "No title found"
        ingredients = [li.get_text().strip() for li in soup.find_all('li') if 'ingredient' in li.get('class', []) or 'ingredient' in li.get_text().lower()]

        return {
            "title": title,
            "date": "2025-06-15",
            "ingredients": ingredients[:15],  # Limit to 15 ingredients for sanity
            "oven": any("oven" in i.lower() for i in ingredients),
            "stove": any("stove" in i.lower() or "pan" in i.lower() for i in ingredients)
        }
    except Exception as e:
        return {"error": str(e), "url": url}

# Example usage:
for url in recipe_links:  # Limit to first 3 to avoid overloading
    print(scrape_recipe(url))

