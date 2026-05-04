# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, OperationalError
from sqlalchemy import text
import re
from db.db import Session as Session
from db.models import ScrapedAuthor
from datetime import datetime
import time

class AbePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item=item)
        
        author = adapter.get("author")
        
        if not author:
            raise DropItem("Missing author")
        
        author = self.clean_author(author=author)
        
        if not self.is_single_author(author=author):
            raise DropItem(f"Multiple authors: {author}")
        
        if self.is_lname_fname(author=author):
            adapter["author"] = self.format_author_fname_lname(author=author)
        
        return item
    
    def clean_author(self, author):
        #remove trailing commas
        author = author.strip('"').strip()
        
        #remove anything after a quote
        author = author.split('"')[0]
        
        author = re.sub(r"\(.*?\)", "", author)
        
        return author.strip()
        
    def is_single_author(self, author):
        
        # obvous multi-author in
        if re.search(r"\b(and|with|et al)\b|[&;]", author.lower()):
            return False
        
        name_pattern = re.findall(r"[A-Za-z]+,\s*[A-Za-z]+", author)
        
        if len(name_pattern) > 1:
            return False
        
        words = author.split()
        capitalized = [w for w in words if w and w[0].isupper()]
        
        if len(capitalized) > 4:
            return False
        
        return True
    
    def is_lname_fname(self, author):
        if author.count(",") != 1:
            return False
            
        lname, fname = [p.strip() for p in author.split(",", 1)]
        
        if not lname or not fname:
            return False
            
        if len(fname.split()) > 3:
            return False
        
        return True
        
    def format_author_fname_lname(self, author):
        lname, fname = [p.strip() for p in author.split(",", 1)]
        return f"{fname} {lname}"
    
class GoodreadsPipeline:
    def __init__(self):
        self.session = Session()
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item=item)
        
        adapter["about_author"] = self.clean_about_author(about_author=adapter["about_author"]) if adapter["about_author"] else None
        adapter["rating"] = self.convert_rating_to_int(rating=adapter["rating"]) if adapter["rating"] else None
        adapter["birthdate"] = self.format_dob(dob=adapter["birthdate"]) if adapter["birthdate"] else None
        adapter["deathdate"] = self.format_death_date(death_date=adapter["deathdate"]) if adapter["deathdate"] else None

        if self.author_exists_in_company_db(author_name=adapter["author"], spider=spider):
            raise DropItem(f"Author {adapter['author']} aleady exists in company db")

        if adapter["rating"] > 4:
            raise DropItem(f"Book rating is greater than 4 in {item}")
        
        return item
    
    def clean_about_author(self, about_author):
        about_author = " ".join(
            t.strip() for t in about_author
            if t.strip()
        )
        
        return about_author
    
    def convert_rating_to_int(self, rating):
        return float(rating)
    
    def check_date_format(self, date_str, format):
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False
        
    def format_dob(self, dob):
        format1 = "%m/%d/%Y"
        format2 = "%B %d, %Y"
        
        if self.check_date_format(date_str=dob, format=format1):
            return datetime.strptime(dob, format1)
        elif self.check_date_format(date_str=dob, format=format2):
            return datetime.strptime(dob, format2)
        else: 
            return None
        
    def format_death_date(self, death_date):
        format1 = "%m/%d/%Y"
        format2 = "%B %d, %Y"
        
        if self.check_date_format(date_str=death_date, format=format1):
            return datetime.strptime(death_date, format1)
        elif self.check_date_format(date_str=death_date, format=format2):
            return datetime.strptime(death_date, format2)
        else:
            return None
        
    def author_exists_in_company_db(self, author_name, spider):
        try:
            # Running a raw SQL query as an example
            result = self.session.execute(
                text(f"SELECT * FROM contacts WHERE name = :name"),
                {"name": author_name}
            ).mappings().first()
            
            return True if result else False
        except Exception as e:
            spider.logger.error(f"{e}")
            return False
            
    def mark_author_as_exists(self, author):
        author.exists_in_company_db = True
        self.session.commit()
        
        
    def close_spider(self, spider):

        ## Close cursor & connection to database 
        self.session.close()
    


class SaveToDBPipeline:
    def __init__(self):
        self.session = Session()
        
    def wait_for_db(self, spider):
        wait_time = 5
        max_wait = 300  # 5 minutes cap
        total_wait = 0

        while total_wait < max_wait:
            try:
                self.session.execute("SELECT 1")
                spider.logger.info("DB restored")
                return

            except Exception:
                spider.logger.warning(f"DB down. Waiting {wait_time}s...")
                time.sleep(wait_time)

                total_wait += wait_time
                wait_time = min(wait_time * 2, 60)

                self.session.close()
                self.session = Session()

        raise Exception("DB did not recover within timeout window")
        
    def process_item(self, item, spider):
        max_retries = 20
        attempt = 0

        while attempt < max_retries:
            try:
                scraped_author = ScrapedAuthor(
                    author=item["author"],
                    about_author=item["about_author"],
                    author_birth_date=item["birthdate"],
                    author_death_date=item["deathdate"],
                    author_website=item["website"],
                    book_url=item["url"],
                    book_title=item["title"],
                    book_rating=item["rating"]
                )

                self.session.add(scraped_author)
                self.session.commit()
                return item

            except IntegrityError:
                self.session.rollback()
                raise DropItem(f"Duplicate author skipped: {item['author']}")

            except (OperationalError, SQLAlchemyError) as e:
                self.session.rollback()
                spider.logger.error(f"DB error: {e}")
                self.wait_for_db(spider)
                return item

            except Exception as e:
                self.session.rollback()
                spider.logger.error(f"Unexpected error: {e}")
                return item

        spider.logger.error("Max retries reached. Skipping item.")
        return item

    def close_spider(self, spider):

        ## Close cursor & connection to database 
        self.session.close()
    