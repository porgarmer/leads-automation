import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import random
import traceback

def create_driver():
    driver = uc.Chrome(headless=False, version_main=146)
    driver.is_closed = True
    return driver

def safe_quit(driver):
    try:
        if driver:
            driver.quit()
    except:
        pass
    
def get_books(driver):
    books = driver.find_elements(By.CSS_SELECTOR, ".product_pod")
    
    results = []
    
    for book in books:
        title = book.find_element(By.TAG_NAME, "h3").text
        price = book.find_element(By.CLASS_NAME, "price_color").text
        rating = book.find_element(By.CLASS_NAME, "star-rating").get_attribute("class")
        
        results.append({
            "title": title,
            "price": price,
            "rating": rating
        })
    
    return results


def main():
    driver = None
    
    try:
        safe_quit(driver)
        driver = create_driver()
        
        base_url = "https://books.toscrape.com/catalogue/page-{}.html"
        
        for page in range(1, 6):  # scrape first 5 pages
            try:
                url = base_url.format(page)
                print(f"\nScraping page {page}: {url}")
                
                driver.get(url)
                
                time.sleep(random.uniform(2, 4))  # human-like delay
                
                books = get_books(driver)
                
                for b in books:
                    print(b)
                
                # restart driver every 3 pages (stability trick)
                if page % 3 == 0:
                    print("Restarting browser...")
                    safe_quit(driver)
                    driver = create_driver()
            
            except Exception as e:
                print("\n=== REAL ERROR ===")
                traceback.print_exc()
                
                # restart driver on error
                safe_quit(driver)
                driver = create_driver()
        safe_quit(driver)
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    main()