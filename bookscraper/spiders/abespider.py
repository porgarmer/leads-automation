import scrapy
from bookscraper.items import ScrapedAuthorItem

class AbeSpider(scrapy.Spider):
    name = "abespider"
    allowed_domains = ["abebooks.com"]
    start_urls = ["https://www.abebooks.com/collections"]
    
    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 1000
    }

    #Get collections view all buttons
    def parse(self, response):
        view_all_links = response.css("[id^='show-all']")
        
        for link in view_all_links:
            href = link.attrib["href"]
            if "collections/browse" in href:
                yield response.follow(href, callback=self.parse_subcategories)
            
    def parse_subcategories(self, response):
        view_all_links = response.css("[id^='show-all']")
        
        for link in view_all_links:
            href = link.attrib["href"]
            if "collections/browse" in href:
                yield response.follow(href, callback=self.parse_collection)

    def parse_collection(self, response):
        collection_links = response.css("div.collection-card a")
        
        for link in collection_links:
            href = link.attrib["href"]
            if "collections/sc" in href:
                yield response.follow(href, callback=self.parse_books)
                
    def parse_books(self, response):
        books = response.css("div.collection-item")
        
        for book in books:
            book_item = BookItem()
            book_item["title"] = book.css("div.title::text").get()
            book_item["author"] = book.css("div.authors::text").get()
            book_item["url"] ="www.abebooks.com" + book.css('div.collection-item  a').attrib['href']
            yield book_item


# def parse(self, response):
#     books = response.css("div.collection-item")
    
#     for book in books:
#         yield{
#             'title' : book.css("div.title::text").get() ,
#             'author' : book.css("div.authors::text").get(),
#             'url' : book.css('div.collection-item  a').attrib['href'],
#         }
            
#VIEW ALL BUTTONS IN COLLECTION PAGE
#response.css("[id^='show-all']")

#VIEW ALL BUTTONS IN SUB COLLECTION PAGE
#response.css("[id^='show-all']")

#COLLECTION LINKS
#collection_links = response.css("div.collection-card a")

#BOOKS
#books = response.css("div.collection-item")


#BOOK TITLE
#book.css("div.title::text").get() 

#BOOK AUTHOR
#book.css("div.authors::text").get()

#BOOK URL
#book.css('div.collection-item  a').attrib['href']