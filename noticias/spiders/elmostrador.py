import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem

class ElMostradorSpider(CrawlSpider):
    name = 'elmostrador'
    item_count = 0
    allowed_domain = ['www.elmostrador.cl']
    start_urls = ['https://www.elmostrador.cl/categoria/pais/']

    # Rules to explore item and next page
    rules = {
        Rule(LinkExtractor(allow='pais/page/'), callback='parse_item', follow=True), # navigation
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//h4[@class="d-tag-card__title"]/a')), # items
             callback='parse_item', follow=False)
    }

    def clean_text(self, text):
        text = ''.join(text)
        text = text.replace("\n", '')
        text = ''.join(text)
        return text.strip()

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'elmostrador'

        # Article title & subtitle
        news_item['title'] = self.clean_text(response.xpath('//h1/text()').extract())
        news_item['subtitle'] = self.clean_text(response.xpath('//p[@class="d-the-single__excerpt | u-fw-600"]/text()').extract())
        if news_item['title'] == "":
            return
        # Article Body (B4S to extract the bold and link texts)
        article_text = ''
        soup = BeautifulSoup(response.body, 'html.parser')
        main_content = soup.find('main')

        paragraphs = main_content.select('p')

        for paragraph in paragraphs:
            text_parts = []
            for element in paragraph.contents:
                if element.name == 'a' or element.name == 'strong':
                    text_parts.append(element.get_text())
                elif isinstance(element, str):
                    text_parts.append(element)
            paragraph_text = ' '.join(text_parts).strip()
            article_text += paragraph_text + ' '

        news_item['body'] = self.clean_text(article_text.strip())

        # Fecha de publicación
        time_element = soup.find('time')

        # Paso 3: Obtener el valor del atributo 'datetime'
        datetime_str = time_element.get('datetime')

        try:
            published_time = datetime.strptime(datetime_str, "%Y-%m-%d")
        except:
            published_time = datetime.strptime(datetime_str, "%d-%m-%Y")
        news_item['date'] = datetime_str
        # URL de la noticia
        news_item['url'] = response.url

        self.item_count += 1
        if self.item_count > 40:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        if days > 1:
            self.item_count += 1
            if self.item_count >= 2:
                raise CloseSpider('Date exceeded')
        yield news_item
