import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text, predict_categories
import pickle
class LaTerceraSpider(CrawlSpider):
    name = 'latercera'
    item_count = 0
    allowed_domain = ['www.latercera.com']
    start_urls = [
        'https://www.latercera.com/categoria/nacional/',
        'https://www.latercera.com/etiqueta/medioambiente/',
        'https://www.latercera.com/etiqueta/seguridad/',
        'https://www.latercera.com/etiqueta/transporte/'
    ]

    with open('./comunas.pkl', 'rb') as f:
        comunas = pickle.load(f)


    rules = {
        Rule(LinkExtractor(allow=(), restrict_xpaths='//div[@class="pagination"]/nav/ul/li/a')),
        Rule(LinkExtractor(allow=(), restrict_xpaths='//div[@class="headline | width_full hl"]/h3/a'),
             callback='parse_item', follow=False)
    }

    def getComunas(self, text):
        comunas_encontradas = [comuna for comuna in self.comunas if comuna in text]
        return comunas_encontradas

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'latercera'

        # Article title & subtitle
        news_item['title'] = clean_text(response.xpath('//*[@id="fusion-app"]/div[1]/section/article/header/div/div[1]/h1/div/text()').extract()[0])
        news_item['subtitle'] = clean_text(response.xpath('//p[@class="excerpt"]/text()').extract()[0])

        # Article Body (B4S to extract the bold and link texts)
        soup = BeautifulSoup(response.body, 'html.parser')
        paragraphs = soup.select('p.paragraph')
        article_text = ''

        for paragraph in paragraphs:
            text_parts = []
            for element in paragraph.contents:
                if element.name == 'a' or element.name == 'b':
                    text_parts.append(element.get_text())
                elif isinstance(element, str):
                    text_parts.append(element)
            paragraph_text = ' '.join(text_parts).strip()
            article_text += paragraph_text + ' '

        news_item['body'] = clean_text(article_text.strip())

        try:
            comunas_encontradas = self.getComunas(news_item['body'])
            news_item['comunas'] = ', '.join(comunas_encontradas)
        except:
            news_item['comunas'] = ''

        # Predecir categorías
        category_1, pred_1, category_2, pred_2 = predict_categories(news_item['body'])
        news_item['category_1'] = category_1
        news_item['pred_1'] = pred_1
        news_item['category_2'] = category_2
        news_item['pred_2'] = pred_2
        
        # Fecha de publicación
        published_time = response.css('meta[property="article:published_time"]::attr(content)').get()
        published_time = datetime.strptime(published_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        news_item['date'] = published_time.strftime("%Y-%m-%d %H:%M:%S")

        # URL de la noticia
        news_item['url'] = response.url

        self.item_count += 1

        if self.item_count > 150:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        
        if days > 1:
            return

        yield news_item
