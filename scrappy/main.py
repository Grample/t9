import json
import scrapy
from scrapy.item import Item, Field
from scrapy.crawler import CrawlerProcess
from itemadapter import ItemAdapter

class QuoteItem(Item):
    author = Field()
    quote = Field()
    tags = Field()  

class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    bio = Field()

class SpiderPipline:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'author' in adapter.keys():
            self.quotes.append({
                'author': adapter['author'],
                'quote': adapter['quote'],
                'tags': adapter['tags'],
            })
        if 'fullname' in adapter.keys():
            self.authors.append({
                'fullname': adapter['fullname'],
                'born_date': adapter['born_date'],
                'born_location': adapter['born_location'],
                'bio': adapter['bio'],
            })       
        return item

    def close_spider(self, spider):
        with open('./json_data/quotes.json', 'w', encoding="utf-8") as file:
            json.dump(self.quotes, file, ensure_ascii=False)
        with open('./json_data/authors.json', 'w', encoding="utf-8") as file:
            json.dump(self.authors, file, ensure_ascii=False)

class Spider(scrapy.Spider):
    name = "my_spider"
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']  
    custom_settings = {SpiderPipline: 300,}

    def parse_author(self, response):
        content = response.xpath('/html//div[@class="author-details"]')
        fullname = content.xpath('h3[@class="author-title"]/text()').get().strip()
        born_date = content.xpath('p/span[@class="author-born-date"]/text()').get().strip()
        born_location = content.xpath('p/span[@class="author-born-location"/text()').get().strip()
        bio = content.xpath('div[@class="author-description"]/text()').get().strip()
        yield AuthorItem(fullname=fullname, born_date=born_date, born_location=born_location, bio=bio)

    def parse_quote(self, response):
        for q in response.xpath('/html//div[@class="quote"]'):
            quote = q.xpath('span[@class="text"]/text()').get().strip()
            author = q.xpath('span/small[@class="author"]/text()').get().strip()
            tags = q.xpath('div[@class="tags"]/a[@class="tag"]/text()').extract()
            yield QuoteItem(author=author, quote=quote, tags=tags)
            yield response.follow(url=self.start_urls[0] + author.xpath('span/a/@href').get(), callback=self.parse_author)
        next_link = response.xpath('/html//li[@class="next"]/a/@href').get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(Spider)
    process.start()