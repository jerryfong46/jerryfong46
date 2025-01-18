# extract/scraper.py

import time
import logging

# Import Selenium libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from typing import List, Dict

def scrape_nba_stats(config: Dict) -> List[Dict]:
    """
    Scrapes NBA player box scores for given seasons and season types.

    Args:
        config (dict): Dictionary containing configuration options such as:
            - nba_stats_url (str): URL of the NBA stats page.
            - seasons (list): List of seasons to scrape (e.g., ['2023', '2024']).
            - season_type (str): Season type (e.g., 'Regular Season').

    Returns:
        list: A list of dictionaries where each dictionary holds the stats for a single game record.
    """

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s'
    )

    # Configuration options
    config = {
        "nba_stats_url": "https://www.nba.com/stats/players/boxscores",
        "seasons": ["2024-25"],
        "season_type": "Regular Season"
    }

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model

    # Set up the Service object with WebDriver Manager
    service = Service(ChromeDriverManager().install())

    # Initialize WebDriver with Service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)

    all_data = []
    try:
        # Navigate to the NBA stats page
        driver.get(config['nba_stats_url'])
        logging.info("Navigated to NBA stats page.")
        time.sleep(5)  # Allow time for page elements to load

        # Iterate over each season if multiple seasons are provided
        seasons = config.get('seasons', [config.get('season')])
        for season in seasons:
            logging.info(f"Processing Season: {season}")

            # Interact with Season dropdown
            try:
                season_dropdown_xpath = "/html/body/div[1]/div[2]/div[2]/div[3]/section[1]/div/div/div[1]/label/div/select"
                season_dropdown_element = driver.find_element("xpath", season_dropdown_xpath)
                select_season = Select(season_dropdown_element)
                select_season.select_by_visible_text(str(season))
                logging.info(f"Selected Season: {season}")
                time.sleep(3)  # Wait for the page to reload with selected season
            except NoSuchElementException:
                logging.error("Season dropdown not found. Check the XPath.")
                continue
            except Exception as e:
                logging.error(f"Error selecting season {season}: {e}")
                continue

            # Interact with Season Type dropdown
            try:
                season_type_dropdown_xpath = "/html/body/div[1]/div[2]/div[2]/div[3]/section[1]/div/div/div[2]/label/div/select"
                season_type_dropdown_element = driver.find_element("xpath", season_type_dropdown_xpath)
                select_season_type = Select(season_type_dropdown_element)
                select_season_type.select_by_visible_text(config['season_type'])
                logging.info(f"Selected Season Type: {config['season_type']}")
                time.sleep(3)  # Wait for the page to reload with selected season type
            except NoSuchElementException:
                logging.error("Season Type dropdown not found. Check the XPath.")
                continue
            except Exception as e:
                logging.error(f"Error selecting season type {config['season_type']}: {e}")
                continue

            # Handle pagination
            while True:
                # Parse current page content
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Locate the stats table (replace with the actual selector if different)
                stats_table = soup.find('table')
                if not stats_table:
                    logging.warning("No table found on the page.")
                    break

                rows = stats_table.find_all('tr')[1:]  # Skip header row if present

                for row in rows:
                    columns = row.find_all('td')
                    if not columns:
                        continue  # Skip if row doesn't have data cells

                    # Example: Adjust indices based on actual table structure
                    try:
                        record = {
                            "game_date": columns[0].get_text(strip=True),
                            "player_name": columns[1].get_text(strip=True),
                            "team": columns[2].get_text(strip=True),
                            "opponent": columns[3].get_text(strip=True),
                            "points": int(columns[4].get_text(strip=True) or 0),
                            "rebounds": int(columns[5].get_text(strip=True) or 0),
                            "assists": int(columns[6].get_text(strip=True) or 0),
                            # Add more stats fields as needed
                        }
                        all_data.append(record)
                    except (IndexError, ValueError) as e:
                        logging.warning(f"Error parsing row data: {e}")
                        continue

                # Check if there's a "next page" button; the logic below depends on the site's layout
                try:
                    next_button_xpath = "/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select"
                    # Alternatively, if it's a button to click, adjust accordingly
                    # For this example, assuming it's a select dropdown for pages
                    page_dropdown_element = driver.find_element("xpath", next_button_xpath)
                    select_page = Select(page_dropdown_element)

                    # Get the current selected page and the total pages
                    selected_option = select_page.first_selected_option
                    current_page = int(selected_option.text)
                    total_pages = len(select_page.options)

                    logging.info(f"Current Page: {current_page} / Total Pages: {total_pages}")

                    if current_page < total_pages:
                        next_page_number = current_page + 1
                        select_page.select_by_visible_text(str(next_page_number))
                        logging.info(f"Navigated to Page: {next_page_number}")
                        time.sleep(3)  # Wait for the page to load
                    else:
                        logging.info("Reached the last page.")
                        break

                except NoSuchElementException:
                    logging.info("Page dropdown not found. Attempting to click 'Next' button instead.")
                    try:
                        next_button = driver.find_element("xpath", "//button[@aria-label='Next']")
                        if 'disabled' in next_button.get_attribute('class'):
                            logging.info("Next button is disabled. Ending pagination.")
                            break
                        next_button.click()
                        logging.info("Clicked Next button.")
                        time.sleep(3)  # Wait for the next page to load
                    except NoSuchElementException:
                        logging.info("No Next button found. Ending pagination.")
                        break
                    except ElementClickInterceptedException as e:
                        logging.error(f"Could not click Next button: {e}")
                        break
                except Exception as e:
                    logging.error(f"Error handling pagination: {e}")
                    break

    finally:
        driver.quit()
        logging.info("WebDriver closed.")

    logging.info(f"Scraping complete. Total records collected: {len(all_data)}")
    return all_data
