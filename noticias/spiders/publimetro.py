import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from datetime import datetime
from bs4 import BeautifulSoup
from noticias.items import NoticiasItem
from noticias.utils import clean_text, predict_categories, preprocesar_texto, setCategories, isGORE
import pickle


class PublimetroSpider(CrawlSpider):
    name = "publimetro"
    allowed_domains = ["publimetro.cl"]
    start_urls = ["https://www.publimetro.cl/noticias/"]
    item_count = 0

    with open('./comunas.pkl', 'rb') as f:
        comunas = pickle.load(f)


    rules = {
        #Rule(LinkExtractor(allow=(), restrict_xpaths='//div[@class="pagination"]/nav/ul/li/a')), //div[contains(@class, 'promo-headline') or contains(@class, 'results-list-container')]//h2
        Rule(LinkExtractor(allow=(), restrict_xpaths='//*[@id="skin-branding"]/div/div[2]/main/div[3]/div/div[2]/a'),
             callback='parse_item', follow=False)
    }

    def getComunas(self, text):
        comunas_encontradas = [comuna for comuna in self.comunas if comuna in text]
        return comunas_encontradas

    def parse_item(self, response):
        news_item = NoticiasItem()
        news_item['media'] = 'publimetro'

        # Article title & subtitle
        news_item['title'] = clean_text(response.xpath('//h1/text()').extract())
        news_item['subtitle'] = clean_text(response.xpath('//div[@class="col-sm-xl-12 layout-section wrap-bottom promo1"]/h2/text()').extract())

        # Article Body (B4S to extract the bold and link texts)
        soup = BeautifulSoup(response.body, 'html.parser')
        content_div = soup.find('article', class_='default__ArticleBody-xb1qmn-2 dwgCRL article-body-wrapper')
        paragraphs = content_div.select('p')
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

        # Preprocesar texto
        news_item['clean_title'] = preprocesar_texto(news_item['title'])
        news_item['clean_subtitle'] = preprocesar_texto(news_item['subtitle'])
        news_item['clean_body'] = preprocesar_texto(news_item['body'])
        
        # Predecir categorías
        # category_1, pred_1, category_2, pred_2 = predict_categories(news_item['body'])
        # news_item['category_1'] = category_1
        # news_item['pred_1'] = pred_1
        # news_item['category_2'] = category_2
        # news_item['pred_2'] = pred_2
        category_1, category_2 = setCategories(news_item['body'])
        news_item['category_1'] = category_1
        news_item['category_1'] = category_2
        
        # GORE
        news_item['gore'] = isGORE(news_item['body'])

        # Sentiment
        news_item['sentiment'] = None
        news_item['POS'] = -1
        news_item['NEU'] = -1
        news_item['NEG'] = -1
        
        # Fecha de publicación
        published_time = response.css('time.primary-font__PrimaryFontStyles-o56yd5-0.ctbcAa.date.undefined::attr(datetime)').get()
        published_time = datetime.strptime(published_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        news_item['date'] = published_time.strftime("%Y-%m-%d %H:%M:%S")

        # URL de la noticia
        news_item['url'] = response.url

        self.item_count += 1

        if self.item_count > 100:
            raise CloseSpider('Item exceeded')
        
        days = (datetime.now().replace(tzinfo=None) - published_time.replace(tzinfo=None)).days
        
        if days > 1:
            return

        yield news_item