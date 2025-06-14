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

url = "https://finance.yahoo.com/quote/" + input_tick + "/analysis"

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Look for the "Top Analysts" section
# Search for this section: <section class="yf-u5azpk" id="top-analyst">
top_analysts_section = soup.find("section", id="top-analyst")
if top_analysts_section:
    print("Found 'Top Analysts' section")
    table_container = top_analysts_section.find_next("div", class_="tableContainer yf-u5azpk")
    if table_container:
        rows = table_container.find_all("tr")
        for row in rows:
            columns = row.find_all("td")
            if columns:
                analyst_name = columns[0].get_text(strip=True)
                if "Morgan Stanley" in analyst_name:
                    print("Morgan Stanley found!")
                    price_target = columns[-2].get_text(strip=True)
                    print(f"Price target: {price_target}")
                    break
        else:
            print("Morgan Stanley not found in this table.")
    else:
        print("Could not find table under Top Analysts section.")
else:
    print("Top Analysts section not found.")