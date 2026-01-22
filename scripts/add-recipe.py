import json
import shutil
import os
from datetime import datetime

file_path = "recipes.json"
backup_dir = "backups"

def load_recipes():
    """Load recipes from the JSON file or return empty list if missing."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: JSON file corrupted. Starting fresh.")
                return []
    return []

def save_recipes(data):
    """Save recipes to JSON, with a backup of the old file."""
    if os.path.exists(file_path):
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"recipes_{timestamp}.json")
        shutil.copy(file_path, backup_file)
        print(f"📂 Backup created: {backup_file}")

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
        print("✅ Recipes updated successfully!")

def add_recipe(recipes):
    """Prompt user for recipe details and add to the list."""
    title = input("Enter recipe title: ").strip()
    date = input("Enter date (YYYY-MM-DD): ").strip()

    ingredients = input("Enter ingredients (comma-separated): ").split(",")
    ingredients = [i.strip() for i in ingredients if i.strip()]

    oven = input("Needs oven? (y/n): ").strip().lower() == "y"
    stove = input("Needs stove? (y/n): ").strip().lower() == "y"
    portions = input("Enter portions: ").strip()

    recipe = {
        "title": title,
        "date": date,
        "ingredients": ingredients,
        "oven": oven,
        "stove": stove,
        "portions": portions
    }

    recipes.append(recipe)
    print(f"🍲 Recipe '{title}' added.")
    return recipes

def menu():
    recipes = load_recipes()

    while True:
        print("\n=== Recipe Manager ===")
        print("1. Add Recipe")
        print("2. View Recipes")
        print("3. Quit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            recipes = add_recipe(recipes)
            save_recipes(recipes)
        elif choice == "2":
            if not recipes:
                print("📭 No recipes found.")
            else:
                for recipe in recipes:
                    print(f"\n📖 {recipe['title']} ({recipe['date']})")
                    print(f"  Portions: {recipe['portions']}")
                    print(f"  Oven: {'Yes' if recipe['oven'] else 'No'}")
                    print(f"  Stove: {'Yes' if recipe['stove'] else 'No'}")
                    print("  Ingredients:")
                    for ing in recipe['ingredients']:
                        print(f"    - {ing}")
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    menu()

