# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    rating = scrapy.Field()
    
    author = scrapy.Field()
    birthdate = scrapy.Field()
    website = scrapy.Field()
    deathdate = scrapy.Field()
    about_author = scrapy.Field()
