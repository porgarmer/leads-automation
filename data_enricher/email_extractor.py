import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import time
import random
import re


def create_driver():
    driver = uc.Chrome(headless=False, version_main=146)
    driver._is_closed = True
    return driver


def random_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))


def normalize_name(name):
    name = name.lower()
    name = re.sub(r'[^a-z\s]', '', name)
    parts = name.split()
    
    return {
        "full": "".join(parts),              # stephenking
        "hyphen": "-".join(parts),          # stephen-king
        "space": " ".join(parts)            # stephen king
    }


def search_author(driver, author_name):
    query = f"{author_name} author"
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    driver.get(search_url)
    random_sleep()
    
    links = driver.find_elements(By.CSS_SELECTOR, "a")
    
    results = []
    
    for link in links:
        href = link.get_attribute("href")
        if href and "http" in href:
            results.append(href)
    
    return results


def extract_domain(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""


def is_author_domain(domain, patterns):
    return (
        patterns["full"] in domain or
        patterns["hyphen"] in domain
    )


def filter_author_website(links, author_name):
    patterns = normalize_name(author_name)
    
    blacklist = [
        "wikipedia", "goodreads", "amazon",
        "facebook", "twitter", "instagram",
        "linkedin", "penguinrandomhouse"
    ]
    
    scored = []
    
    for link in links:
        domain = extract_domain(link)
        
        if not domain:
            continue
        
        if any(b in domain for b in blacklist):
            continue
        
        score = 0
        
        # 🔥 Strong signal: domain contains name
        if is_author_domain(domain, patterns):
            score += 10
        
        # weaker signals
        if patterns["full"] in link:
            score += 5
        
        if domain.endswith(".com"):
            score += 2
        
        scored.append((score, link))
    
    # sort by highest score
    scored.sort(reverse=True, key=lambda x: x[0])
    
    if scored and scored[0][0] > 0:
        return scored[0][1]
    
    return None


def extract_emails_from_text(text):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return list(set(re.findall(email_pattern, text)))


def extract_emails(driver):
    emails = set()
    
    # 1. From page source
    page_source = driver.page_source
    emails.update(extract_emails_from_text(page_source))
    
    # 2. From mailto links
    links = driver.find_elements("tag name", "a")
    
    for link in links:
        href = link.get_attribute("href")
        if href and "mailto:" in href:
            email = href.replace("mailto:", "").split("?")[0]
            emails.add(email)
    
    return list(emails)


def find_contact_page(driver):
    keywords = ["contact", "about", "connect", "email", "reach"]
    
    links = driver.find_elements("tag name", "a")
    
    for link in links:
        text = (link.text or "").lower()
        href = (link.get_attribute("href") or "").lower()
        
        for k in keywords:
            if k in text or k in href:
                print(link.get_attribute("href"))
                return link.get_attribute("href")
    
    return None


def scrape_author_email(author_name):
    driver = create_driver()
    
    try:
        print(f"\nSearching for: {author_name}")
        
        # Step 1: Find website
        links = search_author(driver, author_name)
        website = filter_author_website(links, author_name)
        
        if not website:
            print("No author website found")
            return
        
        print(f"Website: {website}")
        
        # Step 2: Open homepage
        driver.get(website)
        random_sleep()
        
        emails = set()
        
        # Step 3: Extract from homepage
        homepage_emails = extract_emails(driver)
        emails.update(homepage_emails)
        
        print(f"Emails from homepage: {homepage_emails}")
        
        # Step 4: Try contact page if empty
        if not emails:
            contact_page = find_contact_page(driver)
            
            if contact_page:
                print(f"Trying contact page: {contact_page}")
                
                driver.get(contact_page)
                random_sleep()
                
                contact_emails = extract_emails(driver)
                emails.update(contact_emails)
                
                print(f"Emails from contact page: {contact_emails}")
        
        # Final result
        print("\nFINAL EMAILS:")
        print(list(emails))
    
    finally:
        try:
            driver.quit()
        except:
            pass


# TEST
scrape_author_email("Jules Howard")