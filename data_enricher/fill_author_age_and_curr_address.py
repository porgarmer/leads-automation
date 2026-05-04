from db.models import ScrapedAuthor
from db.db import Session
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import spacy
from typing import Optional, Dict, List
from geopy.geocoders import Nominatim, Geolake
import time
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

from config import settings

nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="author-location-parser")


# -----------------------------------
# Trigger Groups
# -----------------------------------

STRONG_LOCATION_TRIGGERS = {
    "lives in": 0.95,
    "currently lives in": 1.00,
    "resides in": 0.95,
    "is based in": 0.92,
    "based in": 0.90,
    "living in": 0.90,
    "now lives in": 0.98,
    "now resides in": 0.98,
    "calls home": 0.85,
    "calls home in": 0.88,
    "makes his home in": 0.88,
    "makes her home in": 0.88,
    "makes their home in": 0.88,
    "home is in": 0.90,
    "has lived in": 0.75,
    "settled in": 0.85,
    "settled down in": 0.88,
    "is settled in": 0.88,
    "located in": 0.82,
    "is located in": 0.82,
    "works and lives in": 0.95,
    "lives and works in": 0.95,
    "currently based in": 0.95,
    "currently residing in": 1.00,
    "currently living in": 1.00,
    "is a resident of": 0.92,
    "remains in": 0.80,
    "stays in": 0.75,
    "dwells in": 0.70
}

MEDIUM_LOCATION_TRIGGERS = {
    "from": 0.45,
    "originally from": 0.50,
    "hails from": 0.52,
    "comes from": 0.45,
    "is from": 0.45,
    "grew up in": 0.35,
    "raised in": 0.35,
    "spent most of his life in": 0.55,
    "spent most of her life in": 0.55,
    "spent years in": 0.50,
    "spent time in": 0.45,
    "works in": 0.60,
    "teaches in": 0.58,
    "writes from": 0.65,
    "writing from": 0.65,
    "reports from": 0.65,
    "operates from": 0.68,
    "runs a studio in": 0.70,
    "maintains a residence in": 0.78,
    "divides time between": 0.72,
    "splits time between": 0.72,
    "travels between": 0.50
}

WEAK_LOCATION_TRIGGERS = {
    "near": 0.25,
    "outside of": 0.30,
    "just outside": 0.30,
    "on the outskirts of": 0.32,
    "in the area of": 0.35,
    "in the region of": 0.38,
    "nearby": 0.20,
    "around": 0.15,
    "close to": 0.25,
    "neighboring": 0.22,
    "surrounded by": 0.18
}

IGNORE_LOCATION_TRIGGERS = [
    "born in",
    "was born in",
    "grew up in",
    "raised in",
    "educated in",
    "studied in",
    "attended school in",
    "graduated from",
    "moved to",
    "moved from",
    "relocated to",
    "lived in during",
    "once lived in",
    "previously lived in",
    "formerly lived in",
    "spent childhood in",
    "started career in",
    "began writing in",
    "worked in",
    "traveled to",
    "visited",
    "vacationed in"
]

# -----------------------------------
# Combine Trigger Dictionary
# -----------------------------------

ALL_TRIGGERS = {}

ALL_TRIGGERS.update(STRONG_LOCATION_TRIGGERS)
ALL_TRIGGERS.update(MEDIUM_LOCATION_TRIGGERS)
ALL_TRIGGERS.update(WEAK_LOCATION_TRIGGERS)

US_STATE_ABBREVIATIONS = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY"
}

US_STATE_CODES = set(US_STATE_ABBREVIATIONS.values())

CITY_CACHE = {}

# -----------------------------------
# Cleaning
# -----------------------------------

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------------
# Find Best Trigger Match
# -----------------------------------

def find_best_trigger(sentence: str):
    sentence_lower = sentence.lower()

    best_trigger = None
    best_score = 0

    for trigger, score in ALL_TRIGGERS.items():
        if trigger in sentence_lower:
            if score > best_score:
                best_trigger = trigger
                best_score = score

    return best_trigger, best_score


# -----------------------------------
# Extract Geo Entities
# -----------------------------------

def extract_geo_entities(sentence: str):
    doc = nlp(sentence)

    locations = []

    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC", "FAC"]:
            locations.append(ent.text)

    return list(dict.fromkeys(locations))


# -----------------------------------
# Main Extraction
# -----------------------------------

def normalize_us_location(location_text):    
    if not location_text:
        return None

    location_text = location_text.strip()

    # -----------------------
    # Case 1: City, State
    # -----------------------

    match = re.match(r"(.+?),\s*([A-Za-z\s]+)$", location_text)

    if match:

        part1 = match.group(1).strip()
        part2 = match.group(2).strip()

        state_lower = part2.lower()

        # Full state name
        if state_lower in US_STATE_ABBREVIATIONS:
            return f"{part1}, {US_STATE_ABBREVIATIONS[state_lower]}"

        # Already abbreviated
        if part2.upper() in US_STATE_CODES:
            return f"{part1}, {part2.upper()}"

    # -----------------------
    # Case 2: State only
    # -----------------------

    lower_text = location_text.lower()

    if lower_text in US_STATE_ABBREVIATIONS:
        return US_STATE_ABBREVIATIONS[lower_text]

    if location_text.upper() in US_STATE_CODES:
        return location_text.upper()

    # -----------------------
    # Case 3: City only
    # -----------------------

    return location_text


# -----------------------------
# Geocode City → Candidate States
# -----------------------------

from typing import List

CITY_CACHE = {}


def get_city_candidates(city_name: str) -> List[str]:

    try:

        city_key = city_name.strip().lower()

        # -------------------------
        # Cache lookup
        # -------------------------
        if city_key in CITY_CACHE:
            return CITY_CACHE[city_key]

        results = geolocator.geocode(
            city_name,
            exactly_one=False,
            addressdetails=True,
            country_codes="us"
        )

        if not results:
            CITY_CACHE[city_key] = []
            return []

        candidates = []

        for loc in results:

            address = loc.raw.get("address", {})

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
            )

            state = address.get("state")

            if city and state:
                formatted = normalize_us_location(f"{city}, {state}")
                candidates.append(formatted)

        # Remove duplicates
        candidates = list(dict.fromkeys(candidates))

        # -------------------------
        # Save to cache
        # -------------------------
        CITY_CACHE[city_key] = candidates

        return candidates

    except Exception:
        return []


# -----------------------------
# Detect City-Only
# -----------------------------
def is_city_only(location_text):

    if not location_text:
        return False

    lower_text = location_text.lower()

    # State-only → NOT city-only
    if lower_text in US_STATE_ABBREVIATIONS:
        return False

    if location_text.upper() in US_STATE_CODES:
        return False

    return "," not in location_text and len(location_text.split()) <= 3


def extract_current_location(text: str) -> Optional[Dict]:

    if not text:
        return None

    text = clean_text(text)

    doc = nlp(text)

    best_result = None

    for sent in doc.sents:

        sentence = sent.text.strip()
        sentence_lower = sentence.lower()

        #Skip historical sentences
        if any(ignore in sentence_lower for ignore in IGNORE_LOCATION_TRIGGERS):
            continue

        trigger, confidence = find_best_trigger(sentence)

        if not trigger:
            continue

        locations = extract_geo_entities(sentence)

        if not locations:
            continue
                
        location = locations[0]
        ambiguous = False
        candidates = []

        if is_city_only(location):

            candidates = get_city_candidates(location)

            if len(candidates) == 1:
                location = candidates[0]

            elif len(candidates) > 1:
                ambiguous = True

        location = normalize_us_location(location)

        result = {
            "location": location,
            "trigger": trigger,
            "sentence": sentence,
            "confidence": round(confidence, 2),
            "ambiguous": ambiguous,
            "candidate_locations": candidates
        }

        # Keep highest confidence match
        if not best_result or confidence > best_result["confidence"]:
            best_result = result

    return best_result

def fill_author_age_and_curr_address(batch_size=100):
    session = Session()
    
    try:
        last_id = 0

        # while True:
        #     authors = (
        #         session.query(ScrapedAuthor)
        #         .filter(ScrapedAuthor.id > last_id) 
        #         .filter_by(to_delete=False, age_and_addr_filled=False, author_death_date=None)
        #         .order_by(ScrapedAuthor.id)
        #         .limit(settings.AGE_ADDRESS_FILL_LIMIT)
        #         .all()
        #     )

        #     if not authors:
        #         break

        #     for author in authors:
        #         author.author_age = calculate_age(author.author_birth_date)

        #         location_data = extract_current_location(author.about_author)
        #         author.author_current_address = (
        #             location_data.get("location") if location_data else None
        #         )
                
        #         author.author_candidate_address = (
        #             location_data.get("candidate_locations") if location_data else None
        #         )
                
        #         author.age_and_addr_filled = True
        #         logging.info(f"{author.author} location and age filled.")

        #         last_id = author.id
                
        #         #time.sleep(1.1)

        #     session.commit()
      
        authors = (
            session.query(ScrapedAuthor)
            #.filter(ScrapedAuthor.id > last_id) 
            .filter_by(to_delete=False, age_and_addr_filled=False, author_death_date=None)
            .order_by(ScrapedAuthor.id)
            .limit(settings.AGE_ADDRESS_FILL_LIMIT)
            .all()
        )

        for author in authors:
            author.author_age = calculate_age(author.author_birth_date)

            location_data = extract_current_location(author.about_author)
            author.author_current_address = (
                location_data.get("location") if location_data else None
            )
            
            author.author_candidate_address = (
                location_data.get("candidate_locations") if location_data else None
            )
            
            author.age_and_addr_filled = True
            logging.info(f"{author.author} location and age filled.")

        session.commit()
        
    except Exception:
        logging.error("An error occured")
        session.rollback()
        raise

    finally:
        session.close()
        
def calculate_age(author_dob):
    if not author_dob:
        return None
    
    current_date = datetime.now(tz=ZoneInfo("Asia/Manila"))
    
    author_age = current_date.year - author_dob.year
    
    if current_date.month > author_dob.month and current_date.day > author_dob.day: 
        author_age+=1
    
    return author_age
    
    
def main():
    fill_author_age_and_curr_address()

if __name__ == "__main__":
    main()