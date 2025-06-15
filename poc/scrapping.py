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

url = "https://www.tipranks.com/stocks/" + input_tick + "/forecast"

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
# save soup to file
with open("soup.html", "w") as file:
    file.write(soup.prettify())

# Look for the "Detailed List of Analyst Forecasts" table
# The new structure uses React Table with rt-tbody class
print("Searching for Detailed List of Analyst Forecasts table...")

# Find the table body with analyst data
table_body = soup.find("div", class_="rt-tbody")
if table_body:
    print("Found analyst forecasts table")
    
    # Find all table rows (rt-tr-group contains each analyst row)
    row_groups = table_body.find_all("div", class_="rt-tr-group")
    
    morgan_stanley_found = False
    for row_group in row_groups:
        # Find the actual row within the group
        row = row_group.find("div", class_="rt-tr")
        if row:
            # Find all table cells
            cells = row.find_all("div", class_="rt-td")
            
            if len(cells) >= 3:  # Make sure we have enough columns
                # Expert Firm is the second column (index 1)
                expert_firm_cell = cells[1]
                expert_firm = expert_firm_cell.get_text(strip=True)
                
                # Check if this row is for Morgan Stanley
                if "Morgan Stanley" in expert_firm:
                    print(f"Found Morgan Stanley analyst!")
                    
                    # Price Target is the third column (index 2)
                    price_target_cell = cells[2]
                    
                    # Look for the price target value within the cell
                    # Handle both single values and ranges (e.g., $80 → $85)
                    price_spans = price_target_cell.find_all("span", class_="Mdcvgxd7")
                    
                    if price_spans:
                        if len(price_spans) == 1:
                            # Single price target
                            price_target = price_spans[0].get_text(strip=True)
                            print(f"Morgan Stanley Price Target: {price_target}")
                        else:
                            # Range: take the higher value (second span)
                            low_target = price_spans[0].get_text(strip=True)
                            high_target = price_spans[1].get_text(strip=True)
                            price_target = f"{low_target} → {high_target} (using {high_target})"
                            print(f"Morgan Stanley Price Target Range: {price_target}")
                        morgan_stanley_found = True
                        break
                    else:
                        # Fallback: get all text from the cell
                        price_target_text = price_target_cell.get_text(strip=True)
                        if price_target_text and price_target_text != "—":
                            # Check if it contains an arrow (range)
                            if "→" in price_target_text or "–" in price_target_text or "-" in price_target_text:
                                print(f"Morgan Stanley Price Target Range: {price_target_text}")
                            else:
                                print(f"Morgan Stanley Price Target: {price_target_text}")
                            morgan_stanley_found = True
                            break
    
    if not morgan_stanley_found:
        print("Morgan Stanley not found in the analyst forecasts table.")
        
        # Debug: Print all expert firms found
        print("\nAll expert firms found:")
        for i, row_group in enumerate(row_groups[:5]):  # Show first 5 for debugging
            row = row_group.find("div", class_="rt-tr")
            if row:
                cells = row.find_all("div", class_="rt-td")
                if len(cells) >= 2:
                    expert_firm = cells[1].get_text(strip=True)
                    print(f"{i+1}. {expert_firm}")
else:
    print("Could not find analyst forecasts table (rt-tbody).")
    
    # Alternative search - look for any table structure
    print("Searching for alternative table structures...")
    all_tables = soup.find_all("table")
    print(f"Found {len(all_tables)} HTML tables")
    
    # Look for any div containing "Morgan Stanley"
    morgan_divs = soup.find_all(text=re.compile("Morgan Stanley", re.IGNORECASE))
    print(f"Found {len(morgan_divs)} references to Morgan Stanley")