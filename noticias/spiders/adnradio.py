import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import predict_categories, preprocesar_texto
import pickle

class ADNRadioSpider(CrawlSpider):
    name = 'adnradio'
    item_count = 0
    allowed_domain = ['www.adnradio.cl']
    start_urls = ['https://www.adnradio.cl/category/nacional/page/1/']

    with open('./comunas.pkl', 'rb') as f:
        comunas = pickle.load(f)

    # Rules to explore item and next page
    rules = {
        Rule(LinkExtractor(allow='nacional/page/'), callback='parse_item', follow=True), # navigation
        Rule(LinkExtractor(allow=(), restrict_xpaths=("//h3/a")), # items
             callback='parse_item', follow=False)
    }

    def clean_text(self, text):
        text = ''.join(text)
        text = text.replace("\n", '')
        text = ''.join(text)
        return text.strip()
    
    def getComunas(self, text):
        comunas_encontradas = [comuna for comuna in self.comunas if comuna in text]
        return comunas_encontradas

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'adnradio'

        # URL de la noticia
        news_item['url'] = response.url

        if '/2023/' not in news_item['url']:
            return
        # Article title & subtitle
        news_item['title'] = self.clean_text(response.xpath('//h1/text()').extract())
        news_item['subtitle'] = self.clean_text(response.xpath('//div[@class="the-single__excerpt"]/p/text()').extract())
        if news_item['title'] == "":
            return
        # Article Body (B4S to extract the bold and link texts)
        soup = BeautifulSoup(response.body, 'html.parser')

        div_element = soup.find('div', class_='the-single__content the-single-content')
        if div_element == None:
            return
        paragraphs = div_element.find_all('p')
        full_text = ''
        for paragraph in paragraphs:
            text_parts = []
            for element in paragraph.contents:
                if element.name == 'a' or element.name == 'strong':
                    text_parts.append(element.get_text())
                elif isinstance(element, str):
                    text_parts.append(element)
            paragraph_text = ' '.join(text_parts).strip()
            full_text += paragraph_text + '\n'

        news_item['body'] = self.clean_text(full_text.strip())

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
        
        # Fecha de publicación
        div_element = soup.find('div', class_='old_post_message')
        year = div_element.get('data-post-year')
        month = div_element.get('data-post-month')
        day = div_element.get('data-post-day')
        datetime_str = '-'.join([year, month, day])
  
        published_time = datetime.strptime(datetime_str, "%Y-%m-%d")
        
        news_item['date'] = published_time

        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        self.item_count += 1
        if self.item_count > 100:
            raise CloseSpider('Item exceeded')
        
        if days > 1:
            # self.item_count += 1
            # if self.item_count > 2:
            #     raise CloseSpider('Date exceeded')
            return
        yield news_item
