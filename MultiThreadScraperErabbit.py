import time
import threading
import queue
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient

class Scraper:
    def __init__(self):
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=firefox_options)

    def fetch_page(self, url):
        self.driver.get(url)
        time.sleep(5)
        return self.driver.page_source

    def close(self):
        self.driver.quit()

def parse_product_page(html, link):
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

def worker(url_queue, result_queue):
    scraper = Scraper()
    while not url_queue.empty():
        url, link = url_queue.get()
        try:
            html = scraper.fetch_page(url)
            product = parse_product_page(html, link)
            result_queue.put(product)
        finally:
            url_queue.task_done()
    scraper.close()

def main(max_links):
    start_time = time.time()
    links = ['https://erabbit.itheima.net/#/category/sub/109243036/' + str(i) for i in range(max_links)]  # 示例链接列表

    url_queue = queue.Queue()
    result_queue = queue.Queue()

    for link in links:
        product_url = f"https://erabbit.itheima.net/{link}"
        url_queue.put((product_url, link))

    threads = []
    for _ in range(10):  # 创建10个线程
        thread = threading.Thread(target=worker, args=(url_queue, result_queue))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    client = MongoClient('mongodb://localhost:27017')
    db = client['products_db']
    collection = db['products']

    while not result_queue.empty():
        product_data = result_queue.get()
        collection.insert_one(product_data)

    total_time = time.time() - start_time
    print(f'Total Execution Time: {total_time} seconds')

if __name__ == '__main__':
    main(50)  # 设置最大links
