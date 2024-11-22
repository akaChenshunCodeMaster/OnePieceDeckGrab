import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from oauth2client.service_account import ServiceAccountCredentials


# Initialize Selenium WebDriver
def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
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
    driver.get(url)
    deck_data = []
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, f"{table_selector} tbody tr")
        for row in rows:
            try:
                deck_name = row.find_element(By.CSS_SELECTOR, "td.column-4").text.strip()
                date = row.find_element(By.CSS_SELECTOR, "td.column-6").text.strip()
                author = row.find_element(By.CSS_SELECTOR, "td.column-8").text.strip()
                tournament = row.find_element(By.CSS_SELECTOR, "td.column-10").text.strip()

                deck_data.append({
                    "deck_name": deck_name,
                    "date": date,
                    "author": author,
                    "tournament": tournament
                })
            except Exception as e:
                print(f"Error extracting row data: {e}")
    except Exception as e:
        print(f"Error scraping deck page: {e}")
    return deck_data


# Check for duplicate decks in the database
def is_duplicate(deck, existing_data):
    for record in existing_data:
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
def update_google_sheet(sheet, deck_data):
    existing_records = sheet.get_all_records()
    if is_duplicate(deck_data, existing_records):
        print(f"Duplicate deck: {deck_data['deck_name']} by {deck_data['author']} on {deck_data['date']} ({deck_data['tournament']}). Skipping.")
    else:
        sheet.append_row([
            deck_data["deck_name"],
            deck_data["date"],
            "",
            deck_data["author"],
            deck_data["tournament"],
            ""
        ])
        print(f"Added deck: {deck_data['deck_name']} by {deck_data['author']} on {deck_data['date']} ({deck_data['tournament']}).")


# Main Function
def main():
    driver = initialize_driver()

    database = {
        "sheet_name": "OP08 English Winning Deck",
        "url": "https://onepiecetopdecks.com/deck-list/english-op-08-two-legends-decks/",
        "table_selector": "#tablepress-23"  # Update if table ID is different
    }

    print(f"Processing database: {database['sheet_name']}")
    sheet = connect_to_google_sheets(database["sheet_name"])
    deck_data = scrape_deck_page(driver, database["url"], database["table_selector"])

    for deck in deck_data:
        update_google_sheet(sheet, deck)

    driver.quit()


if __name__ == "__main__":
    main()
