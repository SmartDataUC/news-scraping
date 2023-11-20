import scrapy
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text, predict_categories
import pickle

class CnnchileSpider(CrawlSpider):
    name = "cnnchile"
    item_count = 0
    allowed_domains = ["www.cnnchile.com"]

    start_urls = [
        'https://www.cnnchile.com/category/pais/'
    ]

    with open('./comunas.pkl', 'rb') as f:
        comunas = pickle.load(f)

    rules = {
        Rule(LinkExtractor(allow=(), restrict_xpaths='/html/body/div[3]/main/div/div[1]/div/div[15]/div[2]/a[3]')),  # navigation
        Rule(LinkExtractor(allow=(), restrict_xpaths='//h2[@class="inner-item__title"]/a'),  # items
             callback='parse_item', follow=False)
    }

    def getComunas(self, text):
        comunas_encontradas = [comuna for comuna in self.comunas if comuna in text]
        return comunas_encontradas
    
    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'cnnchile'
        news_item['url'] = response.url
        
        # Article title & subtitle
        news_item['title'] = clean_text(response.xpath('//h1/text()').extract())
        news_item['subtitle'] = clean_text(response.xpath('//div[@class="main-single-header__excerpt"]/p/text()').extract())
        
        if not news_item['title']:
            return

        # Article Body (B4S to extract the bold and link texts)
        article_text = ''
        soup = BeautifulSoup(response.body, 'html.parser')
        div_element = soup.find('div', class_='main-single-body__content')
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

        # Predecir categorías
        category_1, pred_1, category_2, pred_2 = predict_categories(news_item['body'])
        news_item['category_1'] = category_1
        news_item['pred_1'] = pred_1
        news_item['category_2'] = category_2
        news_item['pred_2'] = pred_2

        json_ld_script = response.css('script[type="application/ld+json"]::text').get()

        
        json_data = json.loads(json_ld_script)

        # Extract the datePublished field
        date_published = json_data.get('datePublished')

        published_time = datetime.strptime(date_published[:10], "%Y-%m-%d")
        news_item['date'] = date_published[:10]

        self.item_count += 1

        if self.item_count > 100:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        
        if days > 1:
            return

        yield news_item

