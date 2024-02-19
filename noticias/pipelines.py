# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import scrapy
from scrapy import signals
from scrapy.exporters import CsvItemExporter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy import Request
import csv
import psycopg2
from noticias.utils import setCategories


class NoticiasPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        file = open('data/%s_items.csv' % spider.name, 'w+b')
        self.files[spider] = file
        self.exporter = CsvItemExporter(file)
        self.exporter.fields_to_export = ['title', 'subtitle', 'body', 'date', 'media', 'url', 'comunas', 'category_1', 'pred_1', 'category_2', 'pred_2']
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class SaveToPSQLPipeline:
    def __init__(self):
        endpoint = "smartdata.cwt3zjjzj7as.sa-east-1.rds.amazonaws.com"
        database = "postgres"
        username = "postgres"
        password = ""
        self.conn = psycopg2.connect(database=database,
                                host=endpoint,
                                user=username,
                                password=password,
                                port="5432")
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        category_1, category_2 = setCategories(item['body'])
        item['category_1'] = category_1
        item['category_2'] = category_2
        self.cursor.execute("""INSERT INTO news(
                            title,
                            subtitle,
                            body,
                            date,
                            media,
                            url,
                            clean_title,
                            clean_subtitle,
                            clean_body,
                            comunas,
                            category_1,
                            category_2,
                            gore,
                            sentiment,
                            pos,
                            neu,
                            neg
                            ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )""", (
                                item['title'], item['subtitle'], item['body'], item['date'], item['media'], item['url'],
                               item['clean_title'], item['clean_subtitle'], item['clean_body'], item['comunas'],
                               item['category_1'], item['category_2'], item['gore'],
                               item['sentiment'], float(item['pos']), float(item['neu']), float(item['neg']) 
                            ))
        self.conn.commit()
        return item
    
    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()