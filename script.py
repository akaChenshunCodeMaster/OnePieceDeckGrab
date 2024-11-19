import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import time

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(), options=options)
    return driver

def connect_to_google_sheets(sheet_name, tab_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(sheet_name)
    sheet = spreadsheet.worksheet(tab_name)
    print(f"Connected to spreadsheet: {sheet_name}, tab: {tab_name}")
    return sheet

def scrape_decklist_links(driver, url):
    driver.get(url)
    deck_links = []
    try:
        links = driver.find_elements(By.CSS_SELECTOR, "div.post-item-content > a")
        for link in links:
            deck_links.append(link.get_attribute("href"))
    except Exception as e:
        print(f"Error while fetching deck links: {e}")
    return deck_links

def scrape_deck_details(driver, deck_url):
    driver.get(deck_url)
    try:
        deck_name = driver.find_element(By.CSS_SELECTOR, "h1.entry-title").text
        author = driver.find_element(By.CSS_SELECTOR, "div.player-name").text
        tournament = driver.find_element(By.CSS_SELECTOR, "div.tournament-details").text
        decklist = driver.find_element(By.CSS_SELECTOR, "pre").text

        return {
            "deck_name": deck_name,
            "author": author,
            "tournament": tournament,
            "decklist": decklist,
        }
    except Exception as e:
        print(f"Error while fetching deck details: {e}")
        return None

def update_google_sheet(sheet, deck_data):
    records = sheet.get_all_records()
    for record in records:
        if (
            record["Deck Name"] == deck_data["deck_name"]
            and record["Author"] == deck_data["author"]
            and record["Tournament"] == deck_data["tournament"]
        ):
            print(f"Deck '{deck_data['deck_name']}' already exists.")
            return False

    sheet.append_row([
        deck_data["deck_name"],
        deck_data["author"],
        deck_data["tournament"],
        deck_data["decklist"],
        "Not Processed"
    ])
    print(f"Added new deck: {deck_data['deck_name']}")
    return True

def main():
    driver = initialize_driver()

    databases = [
        {
            "sheet_name": "OPCG Database",
            "tab_name": "OP09 Japan Winning Deck",
            "url": "https://onepiecetopdecks.com/deck-list/japan-op-09-the-new-emperor-decks/"
        },
        {
            "sheet_name": "OPCG Database",
            "tab_name": "OP08 English Winning Deck",
            "url": "https://onepiecetopdecks.com/deck-list/english-op-08-two-legends-decks/"
        }
    ]

    for db in databases:
        print(f"Processing database: {db['tab_name']}")
        sheet = connect_to_google_sheets(db["sheet_name"], db["tab_name"])
        deck_links = scrape_decklist_links(driver, db["url"])

        for deck_url in deck_links:
            deck_data = scrape_deck_details(driver, deck_url)
            if deck_data:
                update_google_sheet(sheet, deck_data)

    driver.quit()

if __name__ == "__main__":
    main()
