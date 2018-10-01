import requests
from bs4 import BeautifulSoup
import json

# TODO:リクエストエラーのときの処理を考える
r = requests.get('http://traininfo.jreast.co.jp/train_info/kanto.aspx')
soup = BeautifulSoup(r.text, 'lxml')


# TODO:横須賀線は[2]で決め打ちじゃなくて検索して探す。
train = soup.find_all('th', class_='text-tit-xlarge')[2]
train_name = train.text
print(train_name)
train_situation = train.find_next_sibling('td', class_='acess_i').find('img').attrs['alt']
print(train_situation)

train_dict = {}
train_dict['tarin_name'] = train_name
train_dict['train_situation'] = train_situation

# 平常運転の場合はこの下はスキップする
if train_situation != '平常運転':
    # TODO:クラス名は正規表現で取得する。time or time02
    try:
        delivery_time = train.parent.find('td', class_='time').text
    except:
        try:
            delivery_time = train.parent.find('td', class_='time02').text
        except:
            delivery_time = ""

    print(delivery_time)
    cause = train.parent.find_next_sibling('tr').find('td').text
    print(cause)
    train_dict['delivery_time'] = delivery_time
    train_dict['couse'] = cause

with open('info.json') as f:
    data = json.load(f)

before = data['train_situation']
print(before)
print(str(before) == str(train_situation))


# GET前と後で値が変わってたらファイル更新＆LINEに通知
if train_situation != before:
    with open('info.json', 'w') as f:
        json.dump(train_dict, f)

    # LINEに通知
    with open('secret.json') as f:
        data = json.load(f)

    token = data['line_token']
    url = 'https://notify-api.line.me/api/notify'
    header = {'Authorization': 'Bearer ' + token}
    if train_situation == '平常運転':
        option = {'message': '\n' + train_name + '：' + train_situation,
                  'stickerPackageId': 2, 'stickerId': 502}
    else:
        option = {'message': '\n' + train_name + '：' + train_situation + '\n' + cause,
                  'stickerPackageId': 2, 'stickerId': 142}

    response = requests.post(url, data=option, headers=header)
    print(response.text)
