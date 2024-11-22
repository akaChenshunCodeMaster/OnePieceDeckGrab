import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from oauth2client.service_account import ServiceAccountCredentials
import time


# Initialize Selenium WebDriver
def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    return driver


# Connect to Google Sheets
def connect_to_google_sheets(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(credentials)
    sheet = client.open("OPCG Database").worksheet(sheet_name)
    return sheet


# Scrape data from the deck list page
def scrape_deck_page(driver, url, table_selector):
    """
    Scrape all rows from the deck list page and return the extracted data.
    """
    driver.get(url)
    deck_data = []
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, f"{table_selector} tbody tr")
        for row in rows:
            try:
                deck_name = row.find_element(By.CSS_SELECTOR, "td.column-4").text.strip()  # Deck Name
                date = row.find_element(By.CSS_SELECTOR, "td.column-6").text.strip()  # Date
                author = row.find_element(By.CSS_SELECTOR, "td.column-8").text.strip()  # Author
                tournament = row.find_element(By.CSS_SELECTOR, "td.column-10").text.strip()  # Tournament
                detail_link = row.find_element(By.CSS_SELECTOR, "td.column-2 a").get_attribute("href")  # Link

                deck_data.append({
                    "deck_name": deck_name,
                    "date": date,
                    "author": author,
                    "tournament": tournament,
                    "link": detail_link
                })
            except Exception as e:
                print(f"Error extracting row data: {e}")
    except Exception as e:
        print(f"Error scraping deck page: {e}")
    return deck_data


# Scrape decklist from individual page
def scrape_decklist(driver, deck_url):
    """
    Scrape the decklist from the individual deck page.
    """
    driver.get(deck_url)
    try:
        # Scroll down to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Locate the decklist in text
        decklist_section = driver.find_element(By.CSS_SELECTOR, "div#media-gallery").text
        decklist_start = decklist_section.find("Decklist in text:")
        decklist = decklist_section[decklist_start:].replace("Decklist in text:", "").strip()
        return decklist
    except Exception as e:
        print(f"Error fetching decklist: {e}")
        return ""


# Check for duplicate decks in the database
def is_duplicate(deck, existing_data):
    """
    Check if a deck is a duplicate based on deck name, author, date, and tournament.
    """
    for record in existing_data:
        # Normalize and trim all fields to avoid accidental mismatches
        existing_deck_name = record["Deck Name"].strip().lower()
        existing_date = record["Date"].strip()
        existing_author = record["Author"].strip().lower()
        existing_tournament = record["Tournament"].strip().lower()

        if (existing_deck_name == deck["deck_name"].strip().lower() and
                existing_date == deck["date"].strip() and
                existing_author == deck["author"].strip().lower() and
                existing_tournament == deck["tournament"].strip().lower()):
            return True
    return False


# Update Google Sheets with new deck data
def update_google_sheet(sheet, deck_data, decklist):
    """
    Update the Google Sheets database with new deck data if it doesn't already exist.
    """
    existing_records = sheet.get_all_records()  # Get all existing records
    if is_duplicate(deck_data, existing_records):
        print(
            f"Duplicate deck: {deck_data['deck_name']} by {deck_data['author']} on {deck_data['date']} ({deck_data['tournament']}). Skipping.")
    else:
        # Append new row (columns: A=Deck Name, B=Date, C=Decklist, D=Author, E=Tournament, F=Empty)
        sheet.append_row([
            deck_data["deck_name"],
            deck_data["date"],
            decklist,
            deck_data["author"],
            deck_data["tournament"],
            ""  # Column F left empty
        ])
        print(
            f"Added deck: {deck_data['deck_name']} by {deck_data['author']} on {deck_data['date']} ({deck_data['tournament']}).")


# Main Function for Processing Decks
def main():
    # Initialize Selenium WebDriver
    driver = initialize_driver()

    # Define the database and URL
    database = {
        "sheet_name": "OP08 English Winning Deck",
        "url": "https://onepiecetopdecks.com/deck-list/english-op-08-two-legends-decks/",
        "table_selector": "#tablepress-21"  # Update this selector if needed
    }

    print(f"Processing database: {database['sheet_name']}")
    sheet = connect_to_google_sheets(database["sheet_name"])
    deck_data = scrape_deck_page(driver, database["url"], database["table_selector"])

    # Check each deck for duplicates and update the database
    for deck in deck_data:
        decklist = scrape_decklist(driver, deck["link"])
        update_google_sheet(sheet, deck, decklist)

    # Close the WebDriver
    driver.quit()


if __name__ == "__main__":
    main()
