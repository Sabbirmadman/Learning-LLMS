import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Set, List, Optional
from dataclasses import dataclass
from web_scraper.models import WebsiteScrape, ScrapedContent
from vectordb import vector_db
import django
django.setup()

@dataclass
class ScrapedData:
    """Data class to hold scraped content from a webpage"""
    markdown: str = ""
    links: List[str] = None
    images: List[str] = None
    
    def __post_init__(self):
        self.links = self.links or []
        self.images = self.images or []

class WebScraper:
    # File extensions to skip
    SKIP_EXTENSIONS = r'\.(pdf|doc|docx|txt|jpg|jpeg|png|gif|mp4|zip|rar|exe|csv|xls|xlsx|ppt|pptx)$'
    
    def __init__(self, scrape_id: int):
        self.scrape = WebsiteScrape.objects.get(id=scrape_id)
        self.scraped_urls: Set[str] = set()
        self.vector_db_handler = vector_db
        self.base_domain = urlparse(self.scrape.url).netloc

    def start_scraping(self) -> None:
        """Main entry point to start the scraping process"""
        try:
            self.scrape.status = 'IN_PROGRESS'
            self.scrape.save()
            
            self._scrape_page(self.scrape.url)
            
            self.scrape.status = 'COMPLETED'
            self.scrape.save()
        except Exception as e:
            self.scrape.status = 'FAILED'
            self.scrape.save()
            print(f"Error scraping {self.scrape.url}: {str(e)}")

    def _should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped based on various criteria"""
        if url in self.scraped_urls:
            return True
            
        if re.search(self.SKIP_EXTENSIONS, url.lower()):
            return True
            
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ('http', 'https'):
            return True
            
        if parsed_url.netloc != self.base_domain:
            return True
            
        return False

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract valid links from the page"""
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href or '#' in href or 'page=' in href or href.startswith('file://'):
                continue
                
            full_url = urljoin(base_url, href)
            if not self._should_skip_url(full_url):
                links.append(full_url)
        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from the page"""
        return [
            urljoin(base_url, img.get('src'))
            for img in soup.find_all('img')
            if img.get('src')
        ]

    def _clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove unwanted elements from HTML"""
        for footer in soup.find_all(['footer', {'class': 'footer'}, {'id': 'footer'}]):
            footer.decompose()
        return soup

    def _scrape_content(self, url: str, response: requests.Response) -> Optional[ScrapedData]:
        """Scrape content from a single page"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            soup = self._clean_html(soup)
            
            return ScrapedData(
                markdown=soup.get_text(),
                links=self._extract_links(soup, url),
                images=self._extract_images(soup, url)
            )
        except Exception as e:
            print(f"Error parsing content from {url}: {str(e)}")
            return None

    def _save_content(self, url: str, data: ScrapedData, headers: dict) -> None:
        """Save scraped content to database"""
        # Save markdown content
        ScrapedContent.objects.create(
            scrape=self.scrape,
            content_type='MARKDOWN',
            metaData=headers,
            link=url,
            content=data.markdown
        )
        
        # Process markdown for vector database
        self.vector_db_handler.process_markdown(data.markdown, url,  str(self.scrape.id), self.scrape.user_id)
        
        # Save links
        # if data.links:
        #     ScrapedContent.objects.create(
        #         scrape=self.scrape,
        #         content_type='LINK',
        #         metaData=headers,
        #         link=url,
        #         content=', '.join(data.links)
        #     )
        
        # Save images
        # if data.images:
        #     ScrapedContent.objects.create(
        #         scrape=self.scrape,
        #         content_type='IMAGE',
        #         metaData=headers,
        #         link=url,
        #         content=', '.join(data.images)
        #     )

    def _scrape_page(self, url: str) -> None:
        """Scrape a single page and its linked pages"""
        if self._should_skip_url(url):
            return
            
        self.scraped_urls.add(url)
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            scraped_data = self._scrape_content(url, response)
            if scraped_data:
                self._save_content(url, scraped_data, response.headers)
                
                # Recursively scrape linked pages
                for link in scraped_data.links:
                    self._scrape_page(link)
                    
        except requests.exceptions.RequestException as e:
            print(f"Network error scraping {url}: {str(e)}")
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

def scrape_website(scrape_id: int) -> None:
    """Entry point function to start website scraping"""
    scraper = WebScraper(scrape_id)
    scraper.start_scraping()