import undetected_chromedriver as uc
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
import time
import random
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import logging
from db.db import Session
from db.models import ScrapedAuthor, Lead
import traceback
from config import settings
from rapidfuzz import fuzz
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def create_driver():
    
    driver = Driver(uc=True, driver_version=146, headless=False, proxy_pac_url="proxy.pac")
    
    return driver
       
def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))

def human_pause():
    time.sleep(random.uniform(1, 3))
    
def is_blocked(driver):
    title = driver.title.lower()
    page = driver.page_source.lower()
    
    if "just a moment" in title:
        return True
    if "checking your browser" in page:
        return True
    if "cf-challenge" in page:
        return True
    
    return False
    
def remove_trailing_commas(author: str):
    pass

def safe_find_element(driver, by, element, timeout=10):
    try:
        return WebDriverWait(driver=driver, timeout=timeout).until(
            EC.presence_of_element_located((by, element))
        )
    except TimeoutException:
        return None

def get_text(element):
    if element:
        return element.text.split(" +")[0]
    else:
        return None

def get_first_item(driver):
    
    items = WebDriverWait(driver=driver, timeout=10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "search-item"))
    )
    return items[0]

def get_best_possible_match(driver, author):
    
    items = WebDriverWait(driver=driver, timeout=10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "search-item"))
    )
    
    age = author.get("author_age") #this is already an int
    current_address = author.get("author_current_address")
    candidate_addresses = author.get("author_candidate_address") or []
    
    if not age and not current_address and not candidate_addresses:
        return items[0]
    
    best_item = None
    best_score = -1
    
    for item, index in zip(items, range(len(item))):

        score = 0
        try:
            age_elements = item.find_elements(By.CLASS_NAME, "age")

            item_age = None

            if age_elements:
                age_text = age_elements[0].get_attribute("innerText").strip()
                if age_text:
                    try:
                        match = re.search(r"Age\s*(\d+)", age_text)
                        item_age = int(match.group(1)) if match else None
                    except:
                        pass
            
            has_lived_sections = item.find_elements(
                By.XPATH,
                ".//dt[text()='Has lived in:']/parent::dl"
            )

            item_addresses = []

            if has_lived_sections:
                item_addresses = [
                    el.text.strip().lower()
                    for el in has_lived_sections[0].find_elements(By.CSS_SELECTOR, "dd.info")
                ]
            
            # Address match
            if current_address:
                if any((fuzz.partial_ratio(current_address.lower(), a) > 70 for a in item_addresses)):
                #if current_address in item_addresses:
                    score+=50
            
            # Candidate address fallback    
            for addr in candidate_addresses:
                if any((fuzz.partial_ratio(addr.lower(), a) > 70 for a in item_addresses)):
                    score+=35
                    break
            
            # Age match
            if item_age:
                if abs(age - item_age) <= 1:
                       score += 25
            
            # Save best
            if score > best_score:
                best_score = score
                best_item = item
            
            logging.info(f"Best item index: {index}. Age: {age}. Addreses: {item_addresses} Score: {best_score}")
            
        except Exception as e:
            logging.error(e)
            traceback.print_exc(e)
    return best_item if best_item else items[0]

def scrape_author_information(driver, author_name, author):   
    
    try:
        #Go to Veripages homepage
        veripages_url = "https://veripages.com"
        driver.uc_open_with_reconnect(veripages_url, 4)
        human_pause()
        
        #Input the author name in the search bar
        #search_bar = driver.find_element(By.NAME, "name")
        search_bar = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        search_bar.clear()
        human_type(search_bar, author_name)
        human_pause()

        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        button = driver.find_element(By.CLASS_NAME, "form-submitter")
        button.click()
        
        human_pause()
        
        # Check if invalid name message appears
        invalid_name = driver.find_elements(By.CSS_SELECTOR, "div.invalid-feedback")

        if invalid_name:
            print(f"Invalid name: {author_name}")

            search_bar.clear()
            return None
        
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-item"))
        )
        
        #Check if the "No public records found" message exists
        no_records = driver.find_elements(By.CLASS_NAME, "no-records-label")

        if no_records:
            return None

        #Look for best possible match
        item = get_best_possible_match(driver=driver, author=author)
        #item = get_first_item(driver=driver)
        button = item.find_element(By.CLASS_NAME, "view-profile")
        profile_link = button.get_attribute("data-link")
        driver.get(veripages_url+profile_link)
        
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        #Get author address, email, and phone number
        address = safe_find_element(driver=driver, by=By.CSS_SELECTOR, element="dt.p-icon_addr + dd")
        contact_num = safe_find_element(driver=driver, by=By.CSS_SELECTOR, element="dt.p-icon_phone + dd")
        email = safe_find_element(driver=driver, by=By.CSS_SELECTOR, element="dt.p-icon_email + dd")
        
        #Check if the information has contact number. Authors with contact numbers are a priority
        if contact_num:
            return {
                "address": get_text(element=address),
                "contact_num": get_text(element=contact_num),
                "email": get_text(element=email) 
            }
            
        else:
            return None
            
    except Exception as e:
        traceback.print_exc()
        return None
        
def add_lead(session, author, author_info):
    if author_info:
        lead = Lead(
            author=author["author"],
            author_email=author_info["email"],
            author_contact_num=author_info["contact_num"],
            author_address=author_info["address"],
            
            book_url=author["book_url"],
            book_title=author["book_title"],
            book_rating=author["book_rating"],
            
            information_filled=True
        )
    
        session.add(lead)
        
    return None

def update_author_db_record(session, author):
    #After the author is now a lead, set it to be deleted later in the scraped_author table
    author = session.query(ScrapedAuthor).filter_by(id=author["id"]).first()
    if author:
        author.to_delete = True

def main():
    #Get authors from database
    session = Session()
    authors = (
        session.query(ScrapedAuthor)
        .filter_by(to_delete=False, author_death_date=None, age_and_addr_filled=True)
        .limit(settings.VERIPAGES_LIMIT)
    )
    author_information = {}
    driver = create_driver()
    try:
        for author in authors:
            author = author.to_dict()
            print(f"{author}\n")
            author_name = author["author"]
            info = scrape_author_information(driver=driver, author_name=author_name, author=author)
            author_information[author_name] = info
            add_lead(session=session, author=author, author_info=info)
            update_author_db_record(session=session, author=author)
            
            logging.info(f"{author_name}'s information scraped")
            
        session.commit()
        driver.quit()
    except Exception as e:
        traceback.print_exc(e)
        session.rollback()
    
    print(author_information)
  
    
if __name__ == "__main__":
    main()