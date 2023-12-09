import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text, predict_categories, preprocesar_texto
import pickle
class TheClinicSpider(CrawlSpider):
    name = 'theclinic'
    allowed_domains = ['theclinic.cl']
    start_urls = [
        'https://www.theclinic.cl/noticias/tendencias/movilidad/',
        'https://www.theclinic.cl/noticias/actualidad/nacional/'
    ]
    item_count = 0

    with open('./comunas.pkl', 'rb') as f:
        comunas = pickle.load(f)

    rules = (
        Rule(LinkExtractor(allow=(), restrict_xpaths='//a[@class="next page-numbers"]'), follow=True),
        Rule(LinkExtractor(allow=(), restrict_xpaths='//div[@class="titulares"]/h2/a'), callback='parse_item', follow=False),
    )

    def getComunas(self, text):
        comunas_encontradas = [comuna for comuna in self.comunas if comuna in text]
        return comunas_encontradas

    def parse_item(self, response):
        if '/media/' in response.url:
            return

        news_item = NoticiasItem()
        news_item['media'] = 'theclinic'
        news_item['title'] = clean_text(response.css('article.principal h1::text').get())
        news_item['subtitle'] = clean_text(response.css('article.principal p.bajada::text').get())
        news_item['url'] = response.url

        soup = BeautifulSoup(response.body, 'html.parser')
        div_element = soup.find('div', class_='the-content')
        
        if div_element is None:
            return
        
        paragraphs = div_element.find_all('p')
        article_text = ''

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
        
        # Preprocesar texto
        news_item['clean_title'] = preprocesar_texto(news_item['title'])
        news_item['clean_subtitle'] = preprocesar_texto(news_item['subtitle'])
        news_item['clean_body'] = preprocesar_texto(news_item['body'])
        
        # Predecir categorías
        category_1, pred_1, category_2, pred_2 = predict_categories(news_item['body'])
        news_item['category_1'] = category_1
        news_item['pred_1'] = pred_1
        news_item['category_2'] = category_2
        news_item['pred_2'] = pred_2

        date_str = response.css('meta[property="article:published_time"]::attr(content)').get()
        published_time = datetime.strptime(date_str[:10], "%Y-%m-%d")
        news_item['date'] = date_str[:10]

        self.item_count += 1

        if self.item_count > 100:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        
        if days > 1:
            return

        yield news_item
