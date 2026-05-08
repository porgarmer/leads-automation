import scrapy
from bookscraper.items import ScrapedAuthorItem
from datetime import datetime
from scrapy import signals
from scrapy.exceptions import CloseSpider
import psutil
import os
from db.db import Session
from sqlalchemy import text
from config import settings

class GoodreadsSpider(scrapy.Spider):
    name = "goodreads"
    allowed_domains = ["goodreads.com"]
    start_urls = ["https://www.goodreads.com/list/popular_lists"]

    LOCK_ID = 1001

    custom_settings = {
        #"JOBDIR": f"jobs/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        #"JOBDIR": f"jobdir/{name}",
        # "SCHEDULER": "scrapy_redis.scheduler.Scheduler",
        # "DUPEFILTER_CLASS": "scrapy_redis.dupefilter.RFPDupeFilter",
        # "REDIS_URL": "redis://localhost:6379/0",
        "CLOSESPIDER_ITEMCOUNT": settings.SPIDER_LIMIT,
        "ITEM_PIPELINES": {
            "bookscraper.pipelines.GoodreadsPipeline": 300,
            "bookscraper.pipelines.SaveToDBPipeline": 300
        },
         "LINK_EXTRACTORS_ALLOW_DENY": {
            "allow": [r'/author/', r'/list/show/'],
            "deny": [r'/book/show/', r'/work/editions/'],
        },
    }

    def __init__(self):
        super().__init__()
        self.seen_authors = set()
        self.seen_book_urls = set()
        
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        crawler.signals.connect(
            spider.spider_opened,
            signal=signals.spider_opened
        )
        
        crawler.signals.connect(
            spider.spider_closed,
            signal=signals.spider_closed
        )

        return spider
    
    def spider_opened(self):
        # DB lock
        self.db_session = Session()

        # try:
        #     lock_acquired = self.db_session.execute(
        #         text("SELECT pg_try_advisory_lock(:lock_id)"),
        #         {"lock_id": self.LOCK_ID}
        #     ).scalar()

        #     if not lock_acquired:
        #         raise CloseSpider("Another spider instance is already running")

        #     self.logger.info(f"DB lock acquired: {self.LOCK_ID}")

        # except Exception:
        #     self.db_session.close()
        #     raise
        
        try:
            result = self.db_session.execute(
            text("SELECT GET_LOCK(:name, 10)"),
                {"name": self.name}
            ).scalar()

            if result != 1:
                raise CloseSpider("Another spider instance is already running")

            self.logger.info("MySQL lock acquired")
        except Exception:
            self.db_session.close()
            raise
        
    def spider_closed(self, spider):

        if not hasattr(self, "db_session"):
            return

        # try:
        #     self.db_session.execute(
        #         text("SELECT pg_advisory_unlock(:lock_id)"),
        #         {"lock_id": self.LOCK_ID}
        #     )

        #     self.db_session.commit()

        #     self.logger.info(f"DB lock released: {self.LOCK_ID}")

        # except Exception as e:
        #     self.logger.error(f"Failed to release DB lock: {e}")

        # finally:
        #     self.db_session.close()
        try:
            self.db_session.execute(
                text("SELECT RELEASE_LOCK(:name)"),
                {"name": self.name}
            )
            self.db_session.commit()
            self.logger.info("MySQL lock released")
        except Exception as e:
            self.logger.error(f"Failed to release lock: {e}")
        finally:
            self.db_session.close()
            
    def parse(self, response):
        list_links = response.css('a.listTitle')
        
        for link in list_links:
            href = link.attrib["href"]
            yield response.follow(
                href, 
                callback=self.parse_list,
                meta={"depth": 1},
                priority=50,
            )
            
        next_page = response.css("a.next_page::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page, 
                callback=self.parse, 
                priority=10,
                meta={"depth": 1},
            )
            
    def parse_list(self, response):
        book_rows = response.css('tr[itemscope][itemtype="http://schema.org/Book"]')
        
        for book_row in book_rows:
            book_title = book_row.css('a.bookTitle span[itemprop="name"]::text').get()
            book_url = "https://www.goodreads.com" + book_row.css("a.bookTitle::attr(href)").get()
            book_rating =  book_row.css('span.minirating::text').get()
            author_name = book_row.css('a.authorName span[itemprop="name"]::text').get()
            author_link = book_row.css('a.authorName::attr(href)').get()
            
            if not author_link:
                continue  # or self.logger.debug(...)

            if author_link in self.seen_authors:  # ⚠️ Also add dedup back!
                continue
            self.seen_authors.add(author_link)
            
            if book_url in self.seen_book_urls:
                continue
            self.seen_book_urls.add(book_url)
            
            yield response.follow(
                author_link, 
                callback=self.parse_author_page,
                priority=100,
                meta={
                    "book_title": book_title,
                    "book_rating": book_rating,
                    "book_url": book_url,
                    "author_name": author_name,
                    "depth": 0,
                },
            )
        
        next_page = response.css("a.next_page::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page, 
                callback=self.parse_list, 
                priority=-10,
                meta={'depth': response.meta.get('depth', 1) + 1}
            )
        
    # def parse_book_page(self, response):
    #     book_title = response.css('h1[data-testid="bookTitle"]::text').get()
    #     book_rating = response.css("div.RatingStatistics__rating::text").get()
    #     book_url = "https://www.goodreads.com" + response.meta["book_url"]
    #     author_name = response.css("span.ContributorLink__name::text").get()
        
    #     author_link = response.css("a.ContributorLink::attr(href)").get()
        
    #     if not author_link:
    #         self.logger.debug(f"No author link found: {response.url}")
    #         return

    #     if author_link in self.seen_authors:
    #         return

    #     self.seen_authors.add(author_link)

    #     yield response.follow(
    #         author_link, 
    #         callback=self.parse_author_page,
    #         priority=100,
    #         meta={
    #             "book_title": book_title,
    #             "book_rating": book_rating,
    #             "book_url": book_url,
    #             "author_name": author_name,
    #             "depth": 0,
    #         },
    #         errback=self.handle_error
    #     )
        
    def parse_author_page(self, response):
        retry_count = response.meta.get("retry_count", 0)

        author_container_exists = response.css('span[id^="freeTextContainerauthor"]')

        if not author_container_exists:

            if retry_count < 3:
                self.logger.warning(
                    f"Incomplete page, retry {retry_count + 1}: {response.url}"
                )

                yield response.request.replace(
                    dont_filter=True,
                    meta={
                        **response.meta,
                        "retry_count": retry_count + 1
                    }
                )
                return

            self.logger.warning(
                f"Max retries reached. Saving partial author info: {response.url}"
            )

        
        book_title = response.meta["book_title"]
        book_rating = response.meta["book_rating"]
        book_url = response.meta["book_url"]
        
        author_name = response.meta["author_name"]
        
        birth_date = response.css('div[itemprop="birthDate"]::text').get()
        website = response.css('div.dataItem a[itemprop="url"]::attr(href)').get()
        deathdate = response.css('div[itemprop="deathDate"]::text').get()
        
        #Author has nested tags. *::text will get all text including nested tags
        about_author = (
            response.css('span[id^="freeTextauthor"] *::text').getall()
            or response.css('span[id^="freeTextContainerauthor"] *::text').getall()
        )       
        
        scraped_author = ScrapedAuthorItem()
        scraped_author["title"] = book_title
        scraped_author["rating"] = book_rating
        scraped_author["url"] = book_url
        
        scraped_author["author"] = author_name
        scraped_author["birthdate"] = birth_date.strip() if birth_date else None
        scraped_author["website"] = website
        scraped_author["deathdate"] = deathdate.strip() if deathdate else None
        scraped_author["about_author"] = about_author
        
        yield scraped_author

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
       