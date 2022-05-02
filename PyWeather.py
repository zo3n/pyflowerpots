import requests
import json

class PyWeather:

    def __init__(self):
        self.response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={'Zagreb'}&appid={'bf8a214eeb1cb224e7baae9564eddcbb'}&units=metric&lang=hr")
        self.data = json.loads(self.response.text)

    def refreshData(self):
        self.response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={'Zagreb'}&appid={'bf8a214eeb1cb224e7baae9564eddcbb'}&units=metric&lang=hr")
        self.data = json.loads(self.response.text)
        print("refreshed weather data")

    def getTemp(self, round):
        if round:
            return int(self.data["main"]["temp"] + 0.5)
        else:
            return self.data["main"]["temp"]
