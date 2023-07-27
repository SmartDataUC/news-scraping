import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text
import time


class EmolSpider(CrawlSpider):
    name = 'emol'
    allowed_domains = ['emol.com']
    start_urls = ['https://www.emol.com/sitemap/']
    cont = 0
    item_count = 0
    curr_time = time.time()
    # rules = (
    #     # Rule(LinkExtractor(allow=(), restrict_xpaths=(
    #     #     '//a[@class="next current-page-next-prev"]'))),
    #     # Rule(LinkExtractor(allow='noticias/Nacional/', restrict_xpaths=('//div[@class="col_center_noticia4dest-360px bor_destacado"]/h3/a')),
    #     #      callback='parse_item', follow=False)
    #     Rule(LinkExtractor(allow=[r'noticias/' + k + r'/2023/\d{2}/\d{2}/\d+/.*' for k in [
    #         'Nacional']], restrict_xpaths=('//div[@class="col_center_noticia4dest-360px bor_destacado"]/h3/a')),
    #          callback='parse_item', follow=False),
    #     Rule(LinkExtractor(allow=r'.*'), follow=False),
    # )
    rules = (
        Rule(LinkExtractor(
            allow=[r'noticias/[a-zA-Z\d\-]+/\d{4}/\d{2}/\d{2}/\d+/[\da-zA-Z\-]+\.html']),
            callback='parse_item', follow=False),
        Rule(LinkExtractor(
            allow=[
                r'sitemap/noticias/\d{4}/index.html',
                r'sitemap/noticias/\d{4}/emol_noticias.*\.html',
            ],
            deny=[
                r'sitemap/noticias/\d{4}/emol_videos.*\.html',
                r'sitemap/noticias/\d{4}/emol_fotos.*\.html',
            ]), follow=True)
    )

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'emol'
        news_item['title'] = clean_text(response.xpath('//meta[@property="og:title"]/@content').get())
        news_item['url'] = response.xpath('//meta[@property="og:url"]/@content').get()
        news_item['subtitle'] = clean_text(response.xpath('//meta[@property="og:description"]/@content').get())
        
        soup = BeautifulSoup(response.body, 'html.parser')
        div_element = soup.find('div', id='texto_noticia')
        if div_element == None:
            return
        paragraphs = div_element.find_all('div')
        full_text = ''
        for paragraph in paragraphs:
            text_parts = []
            for element in paragraph.contents:
                if element.name == 'a' or element.name == 'b':
                    text_parts.append(element.get_text())
                elif isinstance(element, str):
                    text_parts.append(element)
            paragraph_text = ' '.join(text_parts).strip()
            full_text += paragraph_text + '\n'

        news_item['body'] = clean_text(full_text.strip())


        date_str = response.css('meta[property="article:published_time"]::attr(content)').get()
        published_time = datetime.strptime(date_str[:10], "%Y-%m-%d")
        news_item['date'] = date_str[:10]
        
        stats = self.crawler.stats.get_stats()
        print(f"STASTS RESPON: {stats['response_received_count']}")
        if stats['response_received_count'] > 50:
            raise CloseSpider('Time exceeded')

        self.cont+=1
        if self.cont > 30:
            raise CloseSpider('Date exceeded')
        # days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        # if days > 1:
        #     self.item_count += 1
        #     if self.item_count >= 2:
        #         raise CloseSpider('Date exceeded')
        yield news_item
        