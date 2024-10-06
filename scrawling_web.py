import schedule
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import pymysql
import requests
import os

# cd /Users/dengpeiyu/Desktop/上水汙水處理/rainfall_dect
# python scrawling_web.py


# LINE Notify API
# line_notify_token = 'W4gi0jiVLlXxZl1uy2qBKNyAYgkAHqqk1ZvJXLmuJyU' #個人權杖
# line_notify_token = 'NqYtH8qCmXuA6bH7d9hBQgRUTUL3q4bylrol7rEBjhJ' #測試群組


#文件儲存的相對路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path_station = os.path.join(current_dir, 'static/media', 'stations.txt')
file_path_condition = os.path.join(current_dir, 'static/media', 'condition.txt')
file_path_lineapi = os.path.join(current_dir, 'static/media', 'APIkey.txt')




# 1. line notify request
def line_notify_message(token, message):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {'message': message}
    r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
    return r.status_code

# 2. read txt file
def read_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    return None

# 3. notify messages
def line_notify_if_needed(stations_to_check, df, rainfall_condition):
    # 宣告空陣列
    record_station = []
    rainfall_info = []  # 用於存儲測站及其降雨量
    #read api
    line_notify_token = read_file(file_path_lineapi)

    for station in stations_to_check:
        station_rainfall = df[df['測站名稱'].str.contains(station, regex=False)]
        if not station_rainfall.empty:
            rainfall = station_rainfall.iloc[0]['10分鐘']
            if rainfall is not None:
                try:
                    if float(rainfall) >= float(rainfall_condition):
                        # 將達標測站存成陣列
                        record_station.append(station)
                        # 將測站及其降雨量存入 rainfall_info
                        rainfall_info.append(f"{station}測站降雨量達{rainfall}毫米")
                except ValueError:
                    print(f"{station}測站的降雨量數據無效")
            else:
                message = f"{station}測站無降雨"
                print(message)

    # 只有在有符合条件的站点时
    if rainfall_info:
        # 將所有符合條件的測站及降雨量拼接成一個字串
        stations_list = "\n".join(rainfall_info)
        message = f"\n{stations_list}\n－－－－－－－－－－－－－－－－－－－\n請確認閘門開度是否需要調整。\n\
1. 隨時注意進流水量變化及進流抽水站、調整池水位，視雨量大小控制進流閘門適時調整處理水量。\n\
2. 當雨天（梅雨、颱風、豪大雨）進流水量高於300m³/hr以上時，將逐步調整閘門開度，以確保設備運轉正常。\n\
3. 必要時，得關閉進流閘門，以保護進流抽水站設備。"
        # 發送 Line Notify 訊息
        line_notify_message(line_notify_token, message)
        record_notified_station(record_station)
    else:
        # 如果沒有符合條件的測站，發送一則無測站達標的通知
        record_notified_station("無")



# 4. 存檔案
def record_notified_station(record_station):
    # 直接将列表转换为以逗号分隔的字符串
    txt_content = ",".join(record_station)
    file_dir = os.path.join(current_dir, 'static/media')
    file_name = 'record_notified_station.txt'
    file_path = os.path.join(file_dir, file_name)
    # 將檔案存入
    with open(file_path, 'w') as file:
        file.write(txt_content)


# 5. insert db
def insert_data_to_db(df, connection):
    with connection.cursor() as cursor:
        # 插入数据
        sql_insert = """
        INSERT INTO `rainfall_web` 
        (`station_name`, `region_name`, `rainfall_10min`, `rainfall_1hr`, `rainfall_3hr`,
        `rainfall_6hr`, `rainfall_12hr`, `rainfall_24hr`, `rainfall_2days`, `data_time`, `current_time`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        data_to_insert = [
            (row['測站名稱'], row['行政區'], row['10分鐘'], row['1小時'], row['3小時'], row['6小時'], 
             row['12小時'], row['24小時'], row['2天前'], row['資料時間'], row['當前時間']) 
            for index, row in df.iterrows()
        ]
        cursor.executemany(sql_insert, data_to_insert)



# 6. main function
def fetch_and_store_data():
    
    api_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization=rdec-key-123-45678-011121314"

    # 读取測站
    stations_to_check = read_file(file_path_station)
    if stations_to_check:
        stations_to_check = stations_to_check.strip('[]').replace('"', '').split(',')
        stations_to_check = [station.strip() for station in stations_to_check]

    # 讀取雨量條件
    rainfall_condition = read_file(file_path_condition)

    try:
        # 发起 GET 请求并处理超时
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # 处理数据
        data = response.json()
        records = data.get('records', {}).get('Station', [])
        extracted_data = []

        for location in records:
            if location.get('GeoInfo', {}).get('CountyName', '') == "新竹縣":
                extracted_data.append({
                    '測站名稱': location.get('StationName', 'N/A'),
                    '行政區': location.get('GeoInfo', {}).get('TownName', 'N/A'),
                    '10分鐘': location.get('RainfallElement', {}).get('Past10Min', {}).get('Precipitation', '0'),
                    '1小時': location.get('RainfallElement', {}).get('Past1hr', {}).get('Precipitation', '0'),
                    '3小時': location.get('RainfallElement', {}).get('Past3hr', {}).get('Precipitation', '0'),
                    '6小時': location.get('RainfallElement', {}).get('Past6hr', {}).get('Precipitation', '0'),
                    '12小時': location.get('RainfallElement', {}).get('Past12hr', {}).get('Precipitation', '0'),
                    '24小時': location.get('RainfallElement', {}).get('Past24hr', {}).get('Precipitation', '0'),
                    '2天前': location.get('RainfallElement', {}).get('Past2days', {}).get('Precipitation', '0'),
                    '資料時間': location.get('ObsTime', {}).get('DateTime', 'N/A'),
                    '當前時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        # 创建 DataFrame
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            df = df.replace('-', None)  # 清理和格式化数据
        
        print(df['資料時間'][0])
        print(df['當前時間'][0])
        
        # 连接MySQL
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='1234567=',
            database='water monitor',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        # 检查降雨量并发送通知
        line_notify_if_needed(stations_to_check, df, rainfall_condition)

        # 插入数据到数据库
        insert_data_to_db(df, connection)

        connection.commit()

    except requests.RequestException as e:
        print(f"Request error: {e}")
    except pymysql.MySQLError as e:
        print(f"MySQL error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if connection:
            connection.close()



# 使用 schedule 每10分钟一次
schedule.every(10).minutes.do(fetch_and_store_data)

# 持续运行
while True:
    schedule.run_pending()
    time.sleep(1)
