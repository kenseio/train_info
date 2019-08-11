# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup


# 作業ディレクトリを取得
path = os.path.dirname(os.path.abspath(__file__))
print(path)

# 調べる路線をリストで指定（別ファイルで指定）
f = open(path + '/target.conf', 'r', encoding='utf-8')
data = f.read()

targets = [x.strip() for x in data.split(',')]
# print(targets)

# 前回処理したときの情報を読み込む
try:
    with open(path + '/info.json') as f:
        bef_data = json.load(f)
except:
    bef_data = {}

# JRの運行情報ページへアクセス
r = requests.get('http://traininfo.jreast.co.jp/train_info/kanto.aspx')
soup = BeautifulSoup(r.text, 'html.parser')

# 最初に設定した路線のインデックス(表の何番目に出てくるか)を調べてリストに格納
train_ths = soup.find_all('th', class_='line')
print(len(train_ths))

trains = []
for train_th in train_ths:
    trains.append(train_th.find('p', class_='line_name'))

train_indexes = []
i = 0
for train in trains:
    if train.text in targets:
        # print(train.text, i)
        train_indexes.append(i)
    i += 1
print(train_indexes)

# 取得するインデックス分ループする
train_dict ={}
train_dict['execution_time'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
for train_index in train_indexes:
    train = trains[train_index]
    train_name = train.text
    # print(train_name)
    situation = train.parent.find_next_sibling('td', class_='line_status').find('img').attrs['alt']
    # print(situation)

    train_dict[train_name] = {}
    train_dict[train_name]['train_name'] = train_name
    train_dict[train_name]['situation'] = situation

    # 平常運転の場合は、配信時刻と理由は取得しない
    if situation != '平常運転':
        # 配信時刻のクラス名は正規表現で取得する。time or time02
        delivery_time = train.parent.find('td', class_=re.compile('^time*')).text
        # print(delivery_time)
        cause = train.parent.find_next_sibling('tr').find('td').text
        # print(cause)
    else:
        delivery_time = ''
        cause = ''

    train_dict[train_name]['delivery_time'] = delivery_time
    train_dict[train_name]['cause'] = cause

    # targetを追加したときに前回情報が無いのでエラーにならないようにブランクをセットする
    try:
        bef_situation = bef_data[train_name]['situation']
        bef_cause = bef_data[train_name]['cause']
    except:
        bef_situation = ''
        bef_cause = ''

    # GET前と後で値が変わってたらファイル更新＆LINEに通知
    decision = (bef_situation + bef_cause != situation + cause)
    print(decision)

    if decision:
        print('execute notifier')

        # LINEに通知
        with open(path + '/secret.json') as f:
            data = json.load(f)

        token = data['line_token']
        url = 'https://notify-api.line.me/api/notify'
        header = {'Authorization': 'Bearer ' + token}
        if situation == '平常運転':
            option = {'message': '\n' + train_name + '：' + situation,
                      'stickerPackageId': 2, 'stickerId': 502}
        elif situation == '運転見合わせ':
            option = {'message': '\n' + train_name + '：' + situation + '\n' + cause + '\n' + delivery_time,
                      'stickerPackageId': 2, 'stickerId': 142}
        else:
            option = {'message': '\n' + train_name + '：' + situation + '\n' + cause + '\n' + delivery_time,
                      'stickerPackageId': 2, 'stickerId': 18}

        response = requests.post(url, data=option, headers=header)
        print(response.text)

# 今回の情報をファイルに書き出し
with open(path + '/info.json', 'w') as f:
    json.dump(train_dict, f)
