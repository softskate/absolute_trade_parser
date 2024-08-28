import time
import requests
from database import Product, ProductDetails


class Parser:
    def __init__(self, login, password) -> None:
        self.init(login, password)

    def init(self, login, password):
        headers = {
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'dnt': '1',
            'ecomid': 'https://ecom.elko.ru',
            'origin': 'https://ecom.absoluttrade.ru',
            'priority': 'u=1, i',
            'referer': 'https://ecom.absoluttrade.ru/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        }
        
        pl = {"username": login ,"password": password}
        resp = requests.post('https://api2.absoluttrade.ru/api/Token/CreateToken', json=pl, headers=headers)
        print(resp.status_code, [resp.content])
        self.auth_head = {"Authorization": "Bearer " + resp.text[1:-1]}
        self.last_init = time.time()


    def make_req(self, *args):
        resp = requests.get(*args, headers=self.auth_head)
        print(resp.status_code, len(resp.content))
        if resp.status_code == 200:
            return resp.json()

        else:
            if time.time() - self.last_init < 20:
                print('Rate limit exceeded. Sleeping...')
                time.sleep(10*60)
                
            time.sleep(10)
            self.init()
            return self.make_req(*args)


    def start(self, appid, crawlid):
        def parse_category(categories, parent=None):
            for category in categories:
                _parent = [category['name'], category['code']]
                if parent: _parent = [parent[0] + ' - ' + _parent[0], _parent[1]]

                childs = category['childs']
                if childs:
                    parse_category(childs, _parent)
                else:
                    self.parse_products(*_parent, appid, crawlid)

        params = {
            'tree': True,
            'vendors': False,
            'favorites': False,
            'clientsMenu': False
        }
        js_data = self.make_req('https://api2.absoluttrade.ru/api/Catalogs/CategoryTreeEcom', params)
        parse_category(js_data['categories'])

    def parse_products(self, category_name, category_code, appid, crawlid):
        params = {
            'size': '10',
            'favoriteItems': 'false',
            'categoryCode': category_code,
            'includeNonCondition': 'true',
            'includeEsd': 'false',
            'includeOrdinal': 'true',
            'includeRma': 'true',
            'onlyNew': 'false',
            'currentPage': 1,
            'rowsPerPage': 50,
            'bundlesData.loading': 'false',
            'bundlesData.bundlesList': '',
            'stockTypes.available': 'true',
            'stockTypes.onStock': 'true',
            'stockTypes.transit': 'true',
            'stockTypes.notAvailable': 'true',
            'stockTypes.nonCondition': 'true',
            'stockTypes.spb': 'true',
            'stockTypes.msk': 'true',
            'marketingActivity.id': '0',
            'marketingActivity.isDealer': 'false',
            'onlyDiscounts': 'false',
            'doNotUpdateProducts': 'false',
            'actionType': '1'
        }
        while True:
            js_data = self.make_req('https://api2.absoluttrade.ru/api/Catalogs/GetProducts', params)
            for prod in js_data['products']:
                item = {}
                item['appid'] = appid
                item['crawlid'] = crawlid
                item['productId'] = prod['id']
                item['name'] = prod['name']
                item['price'] = prod['price']
                item['qty'] = prod['quantity']
                item['category'] = category_name
                item['image'] = prod['image']
                item['brandName '] = prod['vendorName']

                Product.create(**item)
                exist = ProductDetails.get_or_none(productId=prod['id'])
                if not exist:
                    self.parse_product_details(prod['id'], appid, crawlid)

            if js_data['from'] + js_data['size'] < js_data['totalCount']:
                params['currentPage'] += 1

            else: break

    def parse_product_details(self, product_id, appid, crawlid):
        js_data = self.make_req(f'https://api2.absoluttrade.ru/api/Catalogs/Products/{product_id}/ProductTableDescription')
        desc = ''
        images = []
        details = {}

        for det in js_data:
            if det['criteria'] == 'Description':
                desc = det['value'.replace('<br', '').replace('/>', '')]

            elif det['criteria'] == 'Image':
                images.append(det['value'])

            else:
                details[det['criteria']] = det['value']

        item = {}
        item['appid'] = appid
        item['crawlid'] = crawlid
        item['productId'] = product_id
        item['imageUrls'] = images
        item['details'] = details
        item['description'] = desc
        ProductDetails.create(**item)
