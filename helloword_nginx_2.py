# -*- coding: utf-8 -*-
#1.导入Flask类
from flask import Flask, jsonify,request
import requests, random, re, time
from HandieJs import Py4Js
from static import setting
from db import RedisClient
from request_proxies import proxies
from multiprocessing import Lock

#2.创建Flask对象接收一个参数__name__，它会指向程序所在的包
app = Flask(__name__)
# logging.basicConfig(filename="D:/flask_translate\loglog.txt", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#3.装饰器的作用是将路由映射到视图函数index
@app.route('/')
def index():
    return 'Hello World'


def is_Chinese(word):
    for ch in word:
        if 'u4e00' <= ch <= 'u9fff':
            return True
    return False


@app.route('/translate', methods=["POST"])
def translate():
    mutex = Lock()
    if request.method == 'POST':
        mutex.acquire()
        content = str(request.form['text'])
        if not is_Chinese(content):
            content = content.lower()
        sizes = re.match('(\d+)[.]{0,1}(\d+)x(\d+)[.]{0,1}(\d+)cm', content.strip().replace(' ', ''))
        if sizes:
            json_dict = {
                "error_code": 0,
                "result": content
            }
            mutex.release()
            return jsonify(json_dict)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), content)
        js = Py4Js()
        tk = js.getTk(content)
        if len(content) > 4891:
            print("翻译的长度超过限制！！！")
            json_dict = {
                "error_code": -1,
                "result": ''
            }
            mutex.release()
            return jsonify(json_dict)
        # redis = RedisClient()
        n = 2
        while True:
            user_agent = random.choice(setting.user_agent_list)
            param = {'tk': tk, 'q': content}
            headers = {
                'user-agent': user_agent,
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'referer': 'https://translate.google.cn/'
            }
            if n:
                try:
                    response = requests.get('http://translate.google.cn/translate_a/single?client=webapp&sl=auto&tl=zh-CN&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&clearbtn=1&otf=1&pc=1&ssel=0&tsel=0&kc=2', params=param, proxies=proxies, headers=headers, timeout=2)
                    if response.status_code == 200:
                        print('数据请求成功')
                        datas = response.json()
                        # print(response.request.url)
                        # print(tk)
                        trans = ''
                        if datas[0]:
                            # print(len(datas[0]))
                            for data in datas[0]:
                                if str(data[0]) == 'None':
                                    continue
                                try:
                                    if '广告' in set(data[0]):
                                        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), datas)
                                        continue
                                    trans += str(data[0])
                                except Exception as e:
                                    print(e)
                        if trans:
                            print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), trans)
                            print(content)
                            json_dict = {
                                "error_code": 0,
                                "result": trans
                            }
                            mutex.release()
                            return jsonify(json_dict)
                        else:
                            print('error_code = -1')
                            json_dict = {
                                "error_code": -1,
                                "result": ''
                            }
                            mutex.release()
                            return jsonify(json_dict)
                except Exception as e:
                    # print(e)
                    # redis.decrease(ip)
                    n -= 1
            else:
                print('error_code = -1')
                json_dict = {
                    "error_code": -1,
                    "result": ''
                }
                mutex.release()
                return jsonify(json_dict)
    else:
        json_dict = {
            "error_code": -1,
            "result": ''
        }
        mutex.release()
        return jsonify(json_dict)

#4.Flask应用程序实例的run方法,启动WEB服务器
if __name__ == '__main__':
    app.run(debug=False, host="100.100.100.100", port=8080)
