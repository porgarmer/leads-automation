import scrapy
from bookscraper.items import ScrapedAuthorItem

class GoodreadsSpider(scrapy.Spider):
    name = "goodreads"
    allowed_domains = ["goodreads.com"]
    start_urls = ["https://www.goodreads.com/list/popular_lists"]

    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 100,
        "ITEM_PIPELINES": {
            "bookscraper.pipelines.GoodreadsPipeline": 300,
            "bookscraper.pipelines.SaveToPostgresPipeline": 300
        }
    }
        
    def parse(self, response):
        list_links = response.css('a.listTitle')
        
        for link in list_links:
            href = link.attrib["href"]
            yield response.follow(href, callback=self.parse_list)
            
        # next_page = response.css("a.next_page::attr(href)").get()
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse)
            
    def parse_list(self, response):
        book_links = response.css("a.bookTitle")
        
        for book_link in book_links:
            href = book_link.attrib["href"]
            yield response.follow(
                href, 
                callback=self.parse_book_page,
                meta={
                    "book_url": href
                }
            )
        
        # next_page = response.css("a.next_page::attr(href)").get()
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse_list)
        
    def parse_book_page(self, response):
        book_title = response.css('h1[data-testid="bookTitle"]::text').get()
        book_rating = response.css("div.RatingStatistics__rating::text").get()
        book_url = "https://www.goodreads.com" + response.meta["book_url"]
        author_name = response.css("span.ContributorLink__name::text").get()
        
        author_link = response.css("a.ContributorLink::attr(href)").get()
        
        yield response.follow(
            author_link, 
            callback=self.parse_author_page,
            meta={
                "book_title": book_title,
                "book_rating": book_rating,
                "book_url": book_url,
                "author_name": author_name
            }
        )
        
    def parse_author_page(self, response):
        if not response.css('span[id^="freeTextContainerauthor"]'):
            self.logger.warning(f"Incomplete page, retrying: {response.url}")
            yield response.request.replace(dont_filter=True)
            return
        
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
        # about_author = " ".join(
        #     t.strip() for t in response.css('span[id^=freeTextContainerauthor] *::text').getall()
        #     if t.strip()
        # )
        
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