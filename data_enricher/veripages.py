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
from db.models import Book

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

def get_first_item(driver):
    items = WebDriverWait(driver=driver, timeout=10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "search-item"))
    )

    return items[0]

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

def scrape_author_information(driver, author):   
    
    try:
        #Go to Veripages homepage
        veripages_url = "https://veripages.com"
        driver.uc_open_with_reconnect(veripages_url, 4)
        human_pause()
        
        #Input the author name in the search bar
        search_bar = driver.find_element(By.NAME, "name")
        search_bar.clear()
        human_type(search_bar, author)
        human_pause()

        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        button = driver.find_element(By.CLASS_NAME, "form-submitter")
        button.click()
        
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-item"))
        )

        #Click the first result
        item = get_first_item(driver=driver)
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
            
    except:
        print("Something went wrong")
        driver.quit()
        
def update_author_db_record(session, author_id, author_info):
    if not author_info:
        return
    
    book = session.query(Book).filter_by(id=author_id).first()
    if book:

        book.author_contact_num = author_info["contact_num"]
        book.author_email = author_info["email"]
        book.author_address = author_info["address"]
        book.information_filled = True
        
        session.commit()
        
def main():
    #Get authors from database
    session = Session()
    authors = session.query(Book).filter_by(information_filled=False).limit(10)
    author_information = {}
    driver = create_driver()

    for author in authors:
        author = author.to_dict()
        info = scrape_author_information(driver=driver, author=author["author"])
        author_information[author["author"]] = info
        update_author_db_record(session=session, author_id=author["id"], author_info=info)
        
    print(author_information)
  
    
if __name__ == "__main__":
    main()