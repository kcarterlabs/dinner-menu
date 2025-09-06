import requests
import time
import os 
import json
from datetime import datetime

api_key = os.getenv('RAPID_API_FORECAST_KEY')

def forecast(date_range):
  print("gathering intel from Big Weather")
  time.sleep(1)
  print(f"Cracking the eggs on your {date_range} day forecast!")
  url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
  querystring = {"q":"Spokane","days":date_range} 
  headers = {
  	"x-rapidapi-key": api_key,
  	"x-rapidapi-host": "weatherapi-com.p.rapidapi.com"
  }
  
  response = requests.get(url, headers=headers, params=querystring)
  data = response.json()
  city = data["location"]["name"]
  region = data["location"]["region"]
  
  print(f"Weather for {city} {region}!")
  formatted = [
    f"{datetime.strptime(day['date'], '%Y-%m-%d').strftime('%A')}: {day['day']['maxtemp_f']}°F"
    for day in data["forecast"]["forecastday"]
  ]
  
  print(formatted)
  weather = formatted
  return weather
  
##############################
##############DEBUG###############
# print(f"Welcome to the Dinner Menu, how many days are you looking to search? (Up to 14)")
# date_range = input("how many days do you want to search for?: ")
# forecast(date_range)
##################################]
##################################
###################################

def dinner_logic(weather, date_range):
    temps = [float(entry.split(':')[1].replace('°F', '').strip()) for entry in weather]
    too_hot = any(temp > 90 for temp in temps)

    with open('recipes.json', 'r') as file:
        data = json.load(file)

    selected_recipes = []
    total_portions = 0
    available_recipes = [r for r in data if not (too_hot and r.get("oven", False))]
    available_recipes.sort(key=lambda r: int(r.get("portions", "1")), reverse=True)

    for recipe in available_recipes:
        portions = int(recipe.get("portions", "1"))
        selected_recipes.append(recipe)
        total_portions += portions

        if int(total_portions) >= int(date_range):
            break

    print(f"\nSelected recipes to cover {date_range} days (total portions = {total_portions}):")

    for recipe in selected_recipes:
        title = recipe["title"]
        ingredients = recipe["ingredients"]
        oven = recipe["oven"]
        stove = recipe["stove"]
        portions = int(recipe.get("portions", "1"))

        print(f"\n{title} - Portions: {portions}")
        print("Ingredients:")
        for ingredient in ingredients:
            print(f"  - {ingredient}")
        print(f"Oven: {'Yes' if oven else 'No'}")
        print(f"Stove: {'Yes' if stove else 'No'}")

while True: 
  print(f"Welcome to the Dinner Menu, how many days are you looking to search? (Up to 14)")

  ####TODO add option block that helps navigate the app and functions
#   option = input("Options: ")
#   option = int(option)

  date_range = input("how many days do you want to search for?: ")
  if int(date_range) <= 14: 
    weather = forecast(date_range)
    dinner_logic(weather, date_range)
  else:
    print(". Fourteen shalt be the highest number thou shalt enter, and the number of thy entering shalt be fourteen or less . fifteen shalt thou not enter")
