from flask import Flask, request
from flask_restful import Resource, Api
import jieba
import json
from aip import AipNlp
import requests

app = Flask(__name__)
api = Api(app)

class SerachES(Resource):

    def __init__(self):
        # 初始化百度客户端
        APP_ID, API_KEY, SECRET_KEY = self.get_api_keys()
        self.client = AipNlp(APP_ID, API_KEY, SECRET_KEY)

        self.req = requests.Session()
        self.url="http://localhost:9200/item_data/datas/_search?"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }
    def get_api_keys(self):
        with open('config/api_key.json', 'r', encoding='utf-8') as r:
            keys = json.load(r)
        return keys['AppId'], keys['ApiKey'], keys['SecretKey']

    def parse_baidu_res(self, res):
        """
        解析百度的分词结果，这里用set的目的是去重
        :param res:
        :return:
        """
        res_set = set()
        res = res['items']
        for word in res:
            item = word['item']
            res_set.add(item)
        return res_set

    def get(self, word, page):
        # 页数如果小于1就指定为1
        if page < 1:
            page = 1
        # 结巴分词
        cut_words = jieba.cut(word)
        cut_words = set(cut_words)
        # 百度api分词
        res = self.client.lexer(word)
        res_set = self.parse_baidu_res(res)
        # 求并集并转化为list
        res_list = list(cut_words | res_set)

        # 构造查询es用的json数据
        # 其中多个关键词用空格表示 或 连接
        query = {"match":{"item_content":" ".join(res_list)}}
        data = {
            "query": query,
            "size": 10, # 每页数据量
            "from": (page - 1) * 10
        }
        # 请求es数据库获得结果
        es_result = self.req.post(url=self.url, data=json.dumps(data), headers=self.headers).content.decode("utf-8")
        es_result = json.loads(es_result)
        # 直接返回es数据库的查询结果
        return es_result

# word:关键字
# page: 页数,每页10条数据
# example: localhost:5000/人工智能/1

api.add_resource(SerachES, '/<string:word>/<int:page>')

if __name__ == '__main__':
    # 配置到服务时debug一定要改为false，开发时可以为true
    app.run(debug=False)