import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()

async def parse_product_page(html, link):
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

async def worker(session, url, link, db):
    html = await fetch_page(session, url)
    product = await parse_product_page(html, link)
    await db.products.insert_one(product)

async def main(max_links):
    start_time = asyncio.get_event_loop().time()
    links = ['https://erabbit.itheima.net/#/category/sub/109243036/' + str(i) for i in range(max_links)]  # 示例链接列表

    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.products_db

    async with aiohttp.ClientSession() as session:
        tasks = [worker(session, f"https://erabbit.itheima.net/{link}", link, db) for link in links]
        await asyncio.gather(*tasks)

    total_time = asyncio.get_event_loop().time() - start_time
    print(f'Total Execution Time: {total_time} seconds')

if __name__ == '__main__':
    asyncio.run(main(50))  # 设置最大links
