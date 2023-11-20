import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text, predict_categories
import pickle
class ElMostradorSpider(CrawlSpider):
    name = 'elmostrador'
    item_count = 0
    allowed_domain = ['www.elmostrador.cl']
    start_urls = [
        'https://www.elmostrador.cl/categoria/pais/',
        'https://www.elmostrador.cl/categoria/agenda-sustentable/'
    ]

    with open('./comunas.pkl', 'rb') as f:
        comunas = pickle.load(f)

    rules = {
        Rule(LinkExtractor(allow=['pais/page/', 'agenda-sustentable/page/'])),  # navigation
        Rule(LinkExtractor(allow=(), restrict_xpaths='//h4[@class="d-tag-card__title"]/a'),  # items
             callback='parse_item', follow=False)
    }

    def getComunas(self, text):
        comunas_encontradas = [comuna for comuna in self.comunas if comuna in text]
        return comunas_encontradas

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'elmostrador'

        # Article title & subtitle
        news_item['title'] = clean_text(response.xpath('//h1/text()').extract())
        news_item['subtitle'] = clean_text(response.xpath('//p[@class="d-the-single__excerpt | u-fw-600"]/text()').extract())
        
        if not news_item['title']:
            return

        # Article Body (B4S to extract the bold and link texts)
        article_text = ''
        soup = BeautifulSoup(response.body, 'html.parser')
        main_content = soup.find('main')
        paragraphs = main_content.select('p')

        for paragraph in paragraphs:
            text_parts = []
            for element in paragraph.contents:
                if element.name in ('a', 'strong'):
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
        time_element = soup.find('time')
        datetime_str = time_element.get('datetime')

        try:
            published_time = datetime.strptime(datetime_str, "%Y-%m-%d")
        except:
            published_time = datetime.strptime(datetime_str, "%d-%m-%Y")

        news_item['date'] = datetime_str

        # URL de la noticia
        news_item['url'] = response.url

        self.item_count += 1
        if self.item_count > 200:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        if days > 1:
            return

        yield news_item
