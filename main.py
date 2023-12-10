import requests
import os
import pandas as pd

def get_lat_lng(api_key, address):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "key": api_key,
        "address": address
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        results = response.json()
        if results["status"] == "OK":
            location = results["results"][0]["geometry"]["location"]
            lat_lng = f"{location['lat']},{location['lng']}"
            return lat_lng
        else:
            print("找不到該地址的座標。")
            return None
    else:
        print("無法取得資料。")
        return None

def find_places_nearby(api_key, target, location):
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        "key": api_key,
        "keyword": target,
        "location": location,
        "language": "zh-TW",
        "radius": 1000,
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        results = response.json()
        # for place in results["results"]:
        #     print(place["name"])
        return len(results["results"])
    else:
        print("無法取得資料。")
        return 0

# 交通
def count_score1(target_dict):
    score = 0
    if target_dict["火車站"] > 0 and target_dict["捷運"] > 0 and target_dict["公車站"] > 0:
        score += 30
    else:
        if target_dict["火車站"] > 0:
            score += 15
        if target_dict["捷運"] > 0:
            score += 10
        if target_dict["公車站"] > 0:
            if target_dict["公車站"] >= 5:
                score += 5
            else:
                score += target_dict["公車站"]

    return score

# 學校
def count_score2(target_dict):
    score = 0
    school_num =  target_dict["國民小學"] + target_dict["國民中學"] +target_dict["高級中學"]
    if school_num >= 2:
        score += 20
    elif school_num == 1:
        score += 10
    return score

# 早餐店
def count_score3(target_dict):
    score = 0
    bf_num = target_dict["早餐店"]
    if bf_num >= 0:
        if bf_num >= 20:
            score = -20
        else:
            score -= bf_num*1
    return score

def count_score4(average):
    score = 0
    if average <= 30:
        score = 20
    elif average <= 50:
        score = 15
    elif average <= 100:
        score = 10
    else:
        score = 5

    return score

def count_score5(total):
    score = 0
    if total <= 8000000:
        score = 2
    elif total <= 14500000:
        score = 5
    elif total <= 21000000:
        score = 8
    else:
        score = 10

    return score

def count_score6(percentage):
    score = 0
    if percentage <= 0.65:
        score = 5
    elif percentage <= 0.70:
        score = 10
    elif percentage <= 0.75:
        score = 15
    else:
        score = 20

    return score

def get_target_info(input_addr):
    target_dict = {
        "火車站": 0,
        "捷運": 0,
        "公車站": 0,
        "國民小學": 0,
        "國民中學": 0,
        "高級中學": 0,
        "早餐店": 0,
    }

    if api_key:
        query = input_addr
        address = f"{query}, 台灣"
        location = get_lat_lng(api_key, address)
        for target in target_dict:
            number = find_places_nearby(api_key, target, location)
            target_dict[target] = number
        print(input_addr, target_dict)
    else:
        print("請設定 MAP_KEY 環境變數。")

    return target_dict

api_key = os.getenv("MAP_KEY")

excel_data = pd.read_excel('place_info.xlsx')
result_data = excel_data.copy()
result_data['15-64歲人口比例'] = result_data['15-64歲人口比例'].str.replace('%', '').astype(float) / 100
for index, row in result_data.iterrows():
    target_dict = get_target_info(row['addr_city']+row['addr_district']+row['addr_village'])
    result_data.at[index, 'score1'] = count_score1(target_dict)
    result_data.at[index, 'score2'] = count_score2(target_dict)
    result_data.at[index, 'score3'] = count_score3(target_dict)
    result_data.at[index, 'score4'] = count_score4(row['每平方公尺/人'])
    result_data.at[index, 'score5'] = count_score5(row['綜稅各類所得金額各縣市鄉鎮村里統計表'])
    result_data.at[index, 'score6'] = count_score6(row['15-64歲人口比例'])

result_data['total score'] = result_data[['score1', 'score2', 'score3', 'score4', 'score5', 'score6']].sum(axis=1)
with pd.ExcelWriter('result_data_with_scores.xlsx') as writer:
    result_data.to_excel(writer, index=False)