# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NoticiasItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    media = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    body = scrapy.Field()
    date = scrapy.Field()
    url = scrapy.Field()
    comunas = scrapy.Field()
    category_1 = scrapy.Field()
    #pred_1 = scrapy.Field()
    category_2 = scrapy.Field()
    #pred_2 = scrapy.Field()
    clean_title = scrapy.Field()
    clean_subtitle = scrapy.Field()
    clean_body = scrapy.Field()
    gore = scrapy.Field()
    sentiment = scrapy.Field()
    POS = scrapy.Field()
    NEU = scrapy.Field()
    NEG = scrapy.Field()
