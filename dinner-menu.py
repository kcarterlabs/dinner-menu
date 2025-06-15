import requests
import time
import os 
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
  return formatted
  
##############################
##############DEBUG###############
# print(f"Welcome to the Dinner Menu, how many days are you looking to search? (Up to 14)")
# date_range = input("how many days do you want to search for?: ")
# forecast(date_range)
##################################]
##################################
###################################

while True: 
  print(f"Welcome to the Dinner Menu, how many days are you looking to search? (Up to 14)")

  ####TODO add option block that helps navigate the app and functions
#   option = input("Options: ")
#   option = int(option)

  date_range = input("how many days do you want to search for?: ")
  if int(date_range) <= 14: 
    forecast(date_range)
  else:
    print(". Fourteen shalt be the highest number thou shalt enter, and the number of thy entering shalt be fourteen or less . fifteen shalt thou not enter")