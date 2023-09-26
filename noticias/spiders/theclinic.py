import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text

class TheClinicSpider(CrawlSpider):
    name = 'theclinic'
    allowed_domains = ['theclinic.cl']
    start_urls = [
        'https://www.theclinic.cl/noticias/tendencias/movilidad/',
        'https://www.theclinic.cl/noticias/actualidad/nacional/'
    ]
    item_count = 0

    rules = (
        Rule(LinkExtractor(allow=(), restrict_xpaths='//a[@class="next page-numbers"]'), follow=True),
        Rule(LinkExtractor(allow=(), restrict_xpaths='//div[@class="titulares"]/h2/a'), callback='parse_item', follow=False),
    )

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
