import numpy as np
import pandas as pd
import os
import requests
import re
from bs4 import BeautifulSoup


# ingredient 변수의 원소값들을 str -> list로 변환
def preprocess_sublist(df, col_name):
    stopword = ["'", '[', ']', ' ']
    sub_list = []
    for i in df[col_name]:
        word = ''
        for k in i:
            if k not in stopword:
                word += k
        sub_list.append(word.split(sep=','))

    res = []
    for i in range(len(df)):
        if len(sub_list[i][0]) == 0 and col_name != 'ingredients.ko':  # 'ingredients.ko' 열의 경우만 처리하지 않도록 수정
            res.append(np.nan)
        else:
            res.append(sub_list[i])

    df[col_name] = res

    return None



### 사용법 df = accessDB.read_db(db_path)
### df에 db가 저장됨
def read_db(path):
    df = pd.read_csv(path, sep='|', header=0).iloc[:, 1:]

    col_list = df.columns[8:14].values
    for i in col_list:
        preprocess_sublist(df, i)

    col_list = ['ingredients.ko', 'ingredients.en', 'ingredients.ja', 'ingredients.zh_CN', 'ingredients.zh_TW', 'allergy.ko', 'allergy.en']

    for col in col_list:
        df[col] = df[col].fillna('[]')

    return df

# 알러지 이미지 return 함수
def find_image(img_path, target):
    target_filename = '{}_image.jpg'.format(target)
    for root, dirs, files in os.walk(img_path):
        if target_filename in files:
            return os.path.join(root, target_filename)
        return print("There's No img in DB")


### 사용법 df_finder('음식명', '원하는 정보', db 저장한 객체명)
def db_finder(food_name, info, df):

    if info == '알러지': # 알러지 한국어.ver
        allergy_list = [y for x in df.loc[(df['ko'] == food_name)]['allergy.ko'] for y in x]
        allergy_data ={
            'image' : ["allergy_image/{}_image.jpg".format(x) for x in allergy_list],
            'description.ko' : allergy_list,
            'description.en' : [y for x in df.loc[(df['ko'] == food_name)]['allergy.en'] for y in x]
        }
        return allergy_data


    elif info == '식재료':
        ingredient_list = [y for x in df.loc[(df['ko'] == food_name)]['ingredients.ko'] for y in x]
        ingredient_data = {
            "image" : ['ingredient_image/{}_image.jpg'.format(x) for x in ingredient_list],
            'description.ko' : ingredient_list,
            'description.en' : [y for x in df.loc[(df['ko'] == food_name)]['ingredients.en'] for y in x],
            'description.ja' : [y for x in df.loc[(df['ko'] == food_name)]['ingredients.ja'] for y in x],
            'description.zh_CN' : [y for x in df.loc[(df['ko'] == food_name)]['ingredients.zh_CN'] for y in x],
            'description.zh_TW' : [y for x in df.loc[(df['ko'] == food_name)]['ingredients.zh_TW'] for y in x]
        }
        return ingredient_data

    elif info == '맵기단계': #맵기 단계 반환
        df['spicy_level'] = df['spicy_level'].apply(lambda x: None if pd.isna(x) or x == np.inf else int(x)).astype('Int64')
        spicy_data =  df[df['ko'] == food_name]['spicy_level']

        if spicy_data.isin([0, 1, 2, 3]).any():
            return spicy_data.item() # 맵기단계가 있을 경우 맵기 단계를 정수형으로 return
        else:
            return None # 맵기단계가 없을 경우 return None


def save_image(food_name, col, df, img_path):

    search_terms = []

    if col == 'ko':
        search_terms.extend(df.loc[df['ko'].isin(food_name)][col])
    else:
        for i in df.loc[df['ko'].isin(food_name)][col].values:
            if isinstance(i, (list, tuple)):
                for j in i:
                    search_terms.append(j)
            else:
                search_terms.append(i)

    if not os.path.exists(img_path):
        os.makedirs(img_path)
    else:
        for f in os.listdir(img_path):
            os.remove(os.path.join(img_path, f))


    url_format = "https://www.google.com/search?q={}&tbm=isch"


    for term in search_terms:
        search_url = url_format.format(term)
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, "html.parser")

        image_links = soup.find_all("img")

        for img in image_links:
            image_url = img.get("src")

            if image_url and not image_url.startswith("data:"):
                if not image_url.startswith("http"):
                    image_url = search_url + image_url
                image_data = requests.get(image_url).content
                image_extension_match = re.search(r"/([a-zA-Z0-9_.-]+)$", image_url)
                if image_extension_match:
                    image_extension = image_extension_match.group(1)
                else:
                    image_extension = "jpg"

                if image_extension.lower() == "jpg":
                    image_filename = f"{img_path}/{term}_image.{image_extension}"

                    with open(image_filename, "wb") as image_file:
                        image_file.write(image_data)
                    break



    # if col == 'allergy':
    #     row = df[df['ko'] == ko] #여기서 df는 read_db로 정제된 df가 되어야 함
    #     allergy = row['allergy'].values[0] #리스트의 첫 str이 결과값으로 들어올 것 
    #     for i in allergy:
    #         display(Image(filename=find_image(image_path, i))) #이미지 display 필요 없으면 삭제
    #         find_image(image_path, i)
    
    # elif col == 'ingredient':
    #     # ingredient_app.py 수정 후 실행하는 코드

    # elif col == 'ko':
    #     # food_app.py 수정 후 실행하는 코드

# 알러지 사진 저장될 경로
# folder_name = r'C:\Users\take0\Desktop\kdata_db\식재료 이미지'
# if not os.path.exists(folder_name):
#     os.makedirs(folder_name)
# else:
#     for f in os.listdir(folder_name):
#         os.remove(os.path.join(folder_name, f))
