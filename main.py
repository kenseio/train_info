import os
import requests
from bs4 import BeautifulSoup
import re
import json

# 調べる路線をリストで指定
targets = ['横須賀線', '南武線', '山手線']

# 作業ディレクトリを取得
path = os.path.dirname(os.path.abspath(__file__))
print(path)

# JRの運行情報ページへアクセス
r = requests.get('http://traininfo.jreast.co.jp/train_info/kanto.aspx')
soup = BeautifulSoup(r.text, 'html.parser')


# 最初に設定した路線のインデックス(表の何番目に出てくるか)を調べてリストに格納
trains = soup.find_all('th', class_='text-tit-xlarge')

train_indexes = []
i = 0
for train in trains:
    if train.text in targets:
        # print(train.text, i)
        train_indexes.append(i)
    i += 1
print(train_indexes)

train_dict ={}

# 取得するインデックス分ループする
for train_index in train_indexes:
    train = trains[train_index]
    train_name = train.text
    # print(train_name)
    situation = train.find_next_sibling('td', class_='acess_i').find('img').attrs['alt']
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

    with open(path + '/info.json') as f:
        data = json.load(f)

    # targetを追加したときに前回情報が無いのでエラーにならないようにブランクをセットする
    try:
        bef_situation = data[train_name]['situation']
        bef_cause = data[train_name]['cause']
    except:
        bef_situation = ''
        bef_cause = ''

    # GET前と後で値が変わってたらファイル更新＆LINEに通知
    decision = (bef_situation + bef_cause != situation + cause)
    print(decision)

    if decision:
        print('execute notifier')
        with open(path + '/info.json', 'w') as f:
            json.dump(train_dict, f)

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
