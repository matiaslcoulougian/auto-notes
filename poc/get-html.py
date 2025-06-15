import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}
input_tick = input("Enter the ticker symbol (e.g., AAPL): ").strip().upper()

url = "https://finance.yahoo.com/quote/" + input_tick

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
# save soup to file
with open("soup.html", "w") as file:
    file.write(soup.prettify())