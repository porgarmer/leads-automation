from db.db import Session
from db.models import Lead
from sqlalchemy import text
import logging
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)
    
#Checks whether that author already exists in the company's records
def author_exists(session, author_name):
    try:
        # Running a raw SQL query as an example
        result = session.execute(
                text(f"SELECT * FROM contacts WHERE name = :name"),
                {"name": author_name}
            ).mappings().first()
            
        return True if result else False
    except Exception as e:
        logging.error(f"{e}")
        return False
    
#mark as exists in company db
def mark_author_as_exists(author):
    logging.info(f"Author {author.author} already exists in company db")
    author.exists_in_company_db = True
    
def get_unexported_authors(session):
    try:
        unexported_authors = (
            session.query(Lead)
            .filter(
                Lead.exported == False
            )
            .limit(settings.EXPORT_LIMIT)
            .all()
        )
        logging.info(f"Fetched {len(unexported_authors)} authors")
        return unexported_authors
    except Exception as e:
        logging.error(f"{e}")
        session.rollback()  # Roll back on error
        
def mark_author_as_exported( author):
    author.exported = True
      
def export_authors():
    
    session = Session()
    
    try:
        unexported_authors = get_unexported_authors(session=session)
        
        export_rows = []
        
        current_date = datetime.now(tz=ZoneInfo("Asia/Manila")).strftime("%d-%m-%Y")
        
        exported = 0
        exists = 0
        for author in unexported_authors:
            
            if author_exists(session=session, author_name=author.author):
                mark_author_as_exists(author=author)
                exists += 1
                continue
            else:
                export_rows.append({
                    "Date": current_date,
                    "Lead Miner": "Rolino Ongco",
                    "Name": author.author,
                    "Book Title": author.book_title,
                    "Phone_Number": author.author_contact_num,
                    "Email": author.author_email,
                    "Address": author.author_address,
                    "Book Link": author.book_url
                })
                mark_author_as_exported(author=author)
                exported += 1
            
        df = pd.DataFrame(export_rows)
        
        if not df.empty:
            file_path = create_filepath(current_date=current_date)
            df.to_excel(file_path, index=False)
            
        session.commit()
            
        logging.info(f"{exists} already exists in the company db. Successfully exported {exported} authors")
    
    except Exception as e:
        session.rollback()
        logging.error(e)

    finally:
        session.close()
        session.close()
    
    
def create_filepath(current_date):
    from pathlib import Path

    output_dir = Path("exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"rolino_leads - {current_date}.xlsx"

    return file_path   

def main():
    export_authors()
    
if __name__ == "__main__":
    main()