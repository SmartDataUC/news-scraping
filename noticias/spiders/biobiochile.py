import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text

class BiobiochileSpider(CrawlSpider):
    name = "biobiochile"
    allowed_domains = ["biobiochile.cl"]
    start_urls = ["https://www.biobiochile.cl/lista/categorias/region-metropolitana"]
    item_count = 0

    # Rules to explore item and next page
    rules = {
        # Rule(LinkExtractor(allow=(), restrict_xpaths=(
        #     '//div[@class="pagination"]/nav/ul/li/a'))),
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//div[@class="article-text-container"]/a')),
             callback='parse_item', follow=False)
    }

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'biobio'
        # Article title & subtitle
        news_item['title'] = clean_text(response.xpath(
            '//h1/text()').extract())
        news_item['subtitle'] = clean_text(response.xpath(
            '//div[@class="post-excerpt"]/p/text()').extract())

        # Article Body (B4S to extract the bold and link texts)
        soup = BeautifulSoup(response.body, 'html.parser')
        id_entry = response.css('meta[name="identrada"]::attr(content)').get()
        div_element = soup.find('div', class_=f'banners-contenido-nota-{id_entry}')
  
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

        news_item['body'] = clean_text(full_text.strip())

        # Fecha de publicación
        date_str = response.css('meta[property="og:updated_time"]::attr(content)').get()
        published_time = datetime.strptime(date_str[:10], "%Y-%m-%d")
        news_item['date'] = date_str[:10]
        # published_time = response.css(
        #     'meta[property="og:updated_time"]::attr(content)').get()
        # published_time = datetime.strptime(
        #     published_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        # news_item['date'] = published_time.strftime("%Y-%m-%d %H:%M:%S")

        # URL de la noticia
        news_item['url'] = response.url

        stats = self.crawler.stats.get_stats()
        if stats['response_received_count'] > 300:
            raise CloseSpider('Time exceeded')
        
        self.item_count += 1
        if self.item_count > 40:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        if days > 1:
            self.item_count += 1
            if self.item_count >= 2:
                raise CloseSpider('Date exceeded')
            return
        yield news_item
