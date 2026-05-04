from db.db import Session as Session
from sqlalchemy import text
from db.models import ScrapedAuthor
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def author_exists(session, author_name):
    try:
        result = session.execute(
            text("SELECT * FROM contacts WHERE name = :name"),
            {"name": author_name}
        ).mappings().first()

        if result:
            logging.info(f"Record in DB: {result['name'], result['email']}")
            return True
        return False

    except Exception as e:
        logging.error(f"{e}")
        return False
    
#mark as exists in company db
def mark_author_as_exists(author):
    logging.info(f"Author {author.author} already exists in company db")
    author.exists_in_company_db = True
    
def main():
    session = Session()
    
    scaped_authors = session.query(ScrapedAuthor).all()
    
    try:
        for author in scaped_authors:
            if author_exists(session=session, author_name=author.author):
                mark_author_as_exists(author=author)
            else:
                logging.info(f"Author {author.author} does not exist in company DB")
        logging.info("About to commit session...")
        session.commit()
        logging.info("Commit successful")
    except Exception as e:
        logging.error(f"{e}")
    finally:
        session.close()
        
main()