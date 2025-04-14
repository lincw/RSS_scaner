import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from pathlib import Path
import logging
import json
from w3lib.html import remove_tags

class MSBSpider(scrapy.Spider):
    name = 'msb_spider'
    start_urls = ['https://www.embopress.org/toc/17444292/current']
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        },
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_TIMEOUT': 30,
    }

    def __init__(self, *args, **kwargs):
        super(MSBSpider, self).__init__(*args, **kwargs)
        self.articles = []

    def parse(self, response):
        # Find all article containers
        article_containers = response.css('div.pb-card, div.issue-items__item')
        
        for article in article_containers:
            # Extract title
            title = article.css('h2.item__title::text, h2.citation__title::text').get()
            if not title:
                continue
            
            # Extract date
            date = article.css('span.epub-section__date::text, time.article-date::text').get()
            
            # Extract abstract URL
            abstract_url = article.css('a[href*="abstract"]::attr(href), a.article-nav__abstract::attr(href)').get()
            
            if abstract_url:
                if not abstract_url.startswith('http'):
                    abstract_url = response.urljoin(abstract_url)
                
                yield scrapy.Request(
                    abstract_url,
                    callback=self.parse_abstract,
                    meta={'title': title.strip(), 'date': date.strip() if date else 'Date not available'},
                    dont_filter=True
                )

    def parse_abstract(self, response):
        title = response.meta['title']
        date = response.meta['date']
        
        # Try different selectors for abstract
        abstract_selectors = [
            'div[class*="abstract"]::text',
            'section[class*="abstract"]::text',
            'div.article-section__abstract::text'
        ]
        
        abstract = None
        for selector in abstract_selectors:
            abstract_parts = response.css(selector).getall()
            if abstract_parts:
                abstract = ' '.join([remove_tags(part).strip() for part in abstract_parts])
                break
        
        if not abstract:
            abstract = "Abstract not available"
        
        article = {
            'title': title,
            'date': date,
            'abstract': abstract
        }
        
        self.articles.append(article)

    def closed(self, reason):
        if self.articles:
            self.create_markdown_report()
        else:
            logging.error("No articles were fetched successfully")

    def create_markdown_report(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        markdown = f"# Molecular Systems Biology - Latest Articles\n\nScanned on: {current_date}\n\n"
        
        for article in self.articles:
            markdown += f"## {article['title']}\n\n"
            markdown += f"**Published:** {article['date']}\n\n"
            markdown += f"**Abstract:**\n{article['abstract']}\n\n"
            markdown += "---\n\n"
        
        self.save_report(markdown)

    def save_report(self, content):
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"msb_articles_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Report saved successfully: {output_path}")
        except Exception as e:
            logging.error(f"Error saving report: {str(e)}")

def main():
    process = CrawlerProcess()
    process.crawl(MSBSpider)
    process.start()

if __name__ == "__main__":
    main()
