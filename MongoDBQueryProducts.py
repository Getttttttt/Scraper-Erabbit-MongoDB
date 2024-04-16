from pymongo import MongoClient
import time

def create_index(collection):
    # 在'name'和'price'字段上创建索引
    name_index = collection.create_index([('name', 1)])
    price_index = collection.create_index([('price', 1)])
    return name_index, price_index

def drop_index(collection, index_name):
    collection.drop_index(index_name)

def query_products(collection, query):
    start_time = time.time()
    results = list(collection.find(query))
    end_time = time.time()
    query_time = end_time - start_time
    return results, query_time

def main():
    client = MongoClient('mongodb://localhost:27017')
    db = client['products_db']
    collection = db['products']

    # 定义查询条件
    product_name = "雨衣"  
    product_price_range = {"$gte": 30, "$lte": 200}  

    # 无索引查询
    print("Querying without indexes...")
    _, query_time_no_index_name = query_products(collection, {'name': product_name})
    _, query_time_no_index_price = query_products(collection, {'price': product_price_range})
    print(f"No index query time for name: {query_time_no_index_name} seconds")
    print(f"No index query time for price range: {query_time_no_index_price} seconds")

    # 创建索引
    print("Creating indexes...")
    name_index, price_index = create_index(collection)

    # 有索引查询
    print("Querying with indexes...")
    _, query_time_index_name = query_products(collection, {'name': product_name})
    _, query_time_index_price = query_products(collection, {'price': product_price_range})
    print(f"Index query time for name: {query_time_index_name} seconds")
    print(f"Index query time for price range: {query_time_index_price} seconds")

    # 移除索引
    drop_index(collection, name_index)
    drop_index(collection, price_index)

if __name__ == '__main__':
    main()
