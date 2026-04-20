import scrapy


class BookFilterSpider(scrapy.Spider):
    name = "book_filter"
    allowed_domains = ["book-filter.com"]
    start_urls = ["https://www.book-filter.com/?maxRating=3&minRatings=0&maxRatings=9000&minYear=2020&minPages=0&__cf_chl_tk=pd7QY9ED3OoNEI35Ccn29Nhj2p0awzuFFRb2WXdCmjg-1776373957-1.0.1.1-RtxlRmTK_upU6WXZGi6LLJ5SO94uOEHkawd77b2QgcA"]

    def parse(self, response):
        book_links = response.css("a.book-card-link")
        
        for book_link in book_links:
            yield{
                "book_link": book_link
            }
