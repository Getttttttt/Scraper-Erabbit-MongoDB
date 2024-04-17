import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient

class Scraper:
    def __init__(self, base_url):
        self.base_url = base_url
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=firefox_options)

    def scroll_to_find_links(self, max_links):
        self.driver.get(self.base_url)
        time.sleep(5)
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        links = []

        while len(links) < max_links:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            last_height = new_height
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            links = list(set(links + [link['href'] for link in soup.find_all('a', class_='goods-item')]))
        
        return links[:max_links]

    def fetch_page(self, url):
        self.driver.get(url)
        time.sleep(5)
        return self.driver.page_source

    def parse_product_page(self, html, link):
        soup = BeautifulSoup(html, 'html.parser')
        ul_tags = soup.find_all('ul', class_='attrs')
        product_detail = {}
        for ul in ul_tags:
            for li in ul.find_all('li'):
                key = li.find('span', class_='dt').text.strip()
                value = li.find('span', class_='dd').text.strip()
                product_detail[key] = value
        style = soup.find('div', class_='goods-image').find('div', class_='large')['style']
        image_link = re.search(r'url\(["\']?(.*?)["\']?\)', style).group(1)
        product = {
            'name': soup.find('p', class_='g-name').text.strip(),
            'price': soup.find('p', class_='g-price').text.strip(),
            'description': soup.find('p', class_='g-desc').text.strip(),
            'link': link,
            'image': image_link,
            'detail': product_detail
        }
        return product

    def close(self):
        self.driver.quit()

def main(max_links):
    start_time = time.time()
    url = 'https://erabbit.itheima.net/#/category/sub/109243036'
    scraper = Scraper(url)
    links = scraper.scroll_to_find_links(max_links)
    print(links)
    
    client = MongoClient('mongodb://localhost:27017')
    db = client['products_db']
    collection = db['products']

    for link in links:
        product_url = f"https://erabbit.itheima.net/{link}"
        product_html = scraper.fetch_page(product_url)
        product_data = scraper.parse_product_page(product_html, link)
        collection.insert_one(product_data)
        print(f'Processed: {product_data["name"]}')

    scraper.close()
    total_time = time.time() - start_time
    print(f'Total Execution Time: {total_time} seconds')

if __name__ == '__main__':
    main(50)  # 设置最大links
