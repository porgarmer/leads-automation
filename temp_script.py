from db.db import Session as PostgreSession
from db.db_company import Session as MySQLSession
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
    postgresession = PostgreSession()
    mysqlsession = MySQLSession()
    
    scaped_authors = postgresession.query(ScrapedAuthor).all()
    
    try:
        for author in scaped_authors:
            if author_exists(session=mysqlsession, author_name=author.author):
                mark_author_as_exists(author=author)
            else:
                logging.info(f"Author {author.author} does not exist in company DB")
        logging.info("About to commit Postgres session...")
        postgresession.commit()
        logging.info("Commit successful")
    except Exception as e:
        logging.error(f"{e}")
    finally:
        postgresession.close()
        
main()