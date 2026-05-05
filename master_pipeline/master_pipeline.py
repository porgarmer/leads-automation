import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    filemode="logs/pipeline.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def run_step(name, command):
    logging.info(f"Staring: {name}")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        logging.error(f"Failed {name}")
        raise Exception(f"Pipeline stopped at {name}")
    
    logging.info(f"Completed {name}")
    

if __name__ == "__main__":
    
    logging.info("Daily pipeline started")
    
    # run_step(
    #     "Scrape Authors",
    #     "scrapy crawl goodreads"
    # )
    
    # run_step(
    #     "Fill Age + Current Address",
    #     "python -m data_enricher.fill_author_age_and_curr_address"
    # )
    
    # run_step(
    #     "Veripages Enrichment",
    #     "python -m data_enricher.veripages"
    # )
    
    run_step(
        "Export to Excel",
        "python -m exporter.exporter"
    )
    
    logging.info("Pipeline completed successully")