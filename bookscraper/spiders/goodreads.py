import scrapy


class GoodreadsSpider(scrapy.Spider):
    name = "goodreads"
    allowed_domains = ["x"]
    start_urls = ["https://x"]

    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 1000
    }
        
    def parse(self, response):
        pass
