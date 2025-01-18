# main.py

import logging
import yaml
from extract.scraper import scrape_nba_stats
from transform.processor import process_data
from load.database import load_to_database
from typing import Dict, List

def load_config(config_path: str = 'config/config.yaml') -> Dict:
    """
    Loads configuration settings from a YAML file.
    
    Args:
        config_path (str): Path to the configuration file.
    
    Returns:
        Dict: Configuration settings.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def setup_logging(log_file: str = 'logs/etl.log'):
    """
    Configures logging settings.
    
    Args:
        log_file (str): Path to the log file.
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

def main():
    """
    Main function to orchestrate the ETL pipeline.
    """
    # Setup logging
    setup_logging()
    logging.info("Starting ETL pipeline")
    
    try:
        # Load configuration
        config = load_config()
        logging.info("Configuration loaded successfully")
        
        # Extract
        logging.info("Starting data extraction")
        raw_data = scrape_nba_stats(config)
        logging.info(f"Data extraction complete. Records extracted: {len(raw_data)}")
        
        # Transform
        logging.info("Starting data transformation")
        transformed_data = process_data(raw_data)
        logging.info(f"Data transformation complete. Records transformed: {len(transformed_data)}")
        
        # Load
        logging.info("Starting data loading")
        load_to_database(transformed_data, config)
        logging.info("Data loading complete")
        
        logging.info("ETL pipeline finished successfully")
    
    except Exception as e:
        logging.error(f"ETL pipeline failed: {e}")
        # Optionally, you can implement notifications here (e.g., send an email or Slack message)
    
if __name__ == "__main__":
    main()
