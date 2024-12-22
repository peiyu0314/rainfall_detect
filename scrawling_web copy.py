import schedule
import time
import pandas as pd
from datetime import datetime
import pymysql
import requests
import os

# =========================
# 文件路徑設置
# =========================
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path_station = os.path.join(current_dir, 'static/media', 'stations.txt')  # 測站清單檔案
file_path_condition = os.path.join(current_dir, 'static/media', 'condition.txt')  # 雨量條件檔案
file_path_lineapi = os.path.join(current_dir, 'static/media', 'APIkey.txt')  # LINE Notify API 權杖檔案
file_path_channel = os.path.join(current_dir, 'static/media', 'channel_token.txt')  # LINE channel_token 權杖檔案
channel_ID = "C81be0403511b941021a10f89f207a880"
enginer_ID = "Cbe41ce7912b29f6f1648949ac03273a8"


# =========================
# 1. 發送 LINE Notify 訊息
# =========================
def line_message_api(channel_access_token, to, message):
    """
    使用 LINE Messaging API 發送訊息
    :param channel_access_token: LINE Messaging API 的 Channel Access Token
    :param to: 接收者的 User ID 或群組 ID
    :param message: 要發送的訊息內容
    :return: API 回應的狀態碼
    """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": "Bearer " + channel_access_token,
        "Content-Type": "application/json"
    }
    payload = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code, response.json()

# =========================
# 2. 讀取文字檔案內容
# =========================
def read_file(file_path):
    """
    讀取指定路徑的文字檔案
    :param file_path: 檔案的路徑
    :return: 檔案內容（若不存在返回 None）
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    return None

# =========================
# 3. 插入通知記錄至 log_table
# =========================
def insert_notify_logs_bulk(connection, notify_log_entries):
    """
    批量插入通知日志
    :param connection: 数据库连接对象
    :param notify_log_entries: 日志条目列表，每个条目是一个元组
    """
    with connection.cursor() as cursor:
        sql_insert_logs = """
        INSERT INTO log_table (station_name, notify_time, rainfall_condition, rainfall_10min, status, error_msg)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(sql_insert_logs, notify_log_entries)
    connection.commit()


# =========================
# 4. 判斷是否發送 LINE 通知
# =========================
def line_notify_if_needed(stations_to_check, df, rainfall_condition, connection):
    # 初始化记录
    rainfall_info = []  # 达标测站的通知内容
    log_info = []  # 错误或未达标的测站记录
    notify_log_entries = []  # 用于存储日志条目
    line_notify_token = read_file(file_path_channel)

    for station in stations_to_check:
        try:
            # 检查测站数据是否存在
            station_data = df[df['測站名稱'].str.contains(station, regex=False)]
            notify_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if station_data.empty:
                log_message = f"{station} 測站資料不存在"
                log_info.append(log_message)
                notify_log_entries.append((station, notify_time, rainfall_condition, None, 0, log_message))
                continue

            # 提取雨量数据
            rainfall = station_data.iloc[0]['10分鐘']

            # 判断雨量是否达标
            if float(rainfall) >= float(rainfall_condition):
                message = f"{station}測站降雨量達 {rainfall} 毫米"
                rainfall_info.append(message)
                notify_log_entries.append((station, notify_time, rainfall_condition, float(rainfall), 1, message))

        except (ValueError, TypeError) as e:
            error_message = f"{station} 測站數據異常，錯誤訊息: {str(e)}"
            log_info.append(error_message)
            notify_log_entries.append((station, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        rainfall_condition, None, 0, error_message))

    # 批量插入日志
    insert_notify_logs_bulk(connection, notify_log_entries)

    # 发送通知
    if rainfall_info:
        send_success_notification(line_notify_token, rainfall_info)
    if log_info:
        send_error_notification(line_notify_token, log_info)


# sucess notify
def send_success_notification(token, messages):
    """
    發送成功通知
    :param token: LINE Notify Token
    :param messages: 達標測站訊息
    """
    message = "\n".join(messages)
    detailed_message = f"{message}\n－－－－－－－－－－－－－－－－－－－\n請確認閘門開度是否需要調整。\n\
1. 隨時注意進流水量變化及進流抽水站、調整池水位，視雨量大小控制進流閘門適時調整處理水量。\n\
2. 當雨天（梅雨、颱風、豪大雨）進流水量高於300m³/hr以上時，將逐步調整閘門開度，以確保設備運轉正常。\n\
3. 必要時，得關閉進流閘門，以保護進流抽水站設備。"
    line_message_api(token, channel_ID, detailed_message)
    print("達標通知已發送")

# error notify
def send_error_notification(token, errors):
    """
    發送錯誤通知
    :param token: LINE Notify Token
    :param errors: 錯誤或未達標訊息（列表）
    """
    message = "工程團隊通知：\n" + "\n".join(errors)
    line_message_api(token, enginer_ID, message)
    print("錯誤通知已發送")



# =========================
# 5. 將數據插入 rainfall_web 表
# =========================
def insert_data_to_db(df, connection):
    """
    將測站數據插入 rainfall_web 表
    :param df: 爬取的測站數據 DataFrame
    :param connection: MySQL 連接對象
    """
    with connection.cursor() as cursor:
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



# =========================
# 6. 存檔案
# =========================
def record_notified_station(record_station):
    # 直接将列表转换为以逗号分隔的字符串
    txt_content = ",".join(record_station)
    file_dir = os.path.join(current_dir, 'static/media')
    file_name = 'record_notified_station.txt'
    file_path = os.path.join(file_dir, file_name)
    # 將檔案存入
    with open(file_path, 'w') as file:
        file.write(txt_content)

# =========================
# 7. 主函式：抓取數據、檢查與通知
# =========================
def fetch_and_store_data():
    """
    從氣象局 API 抓取數據，檢查降雨量，發送通知，並存儲數據到資料庫
    """
    api_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization=rdec-key-123-45678-011121314"
    # 读取測站
    stations_to_check = read_file(file_path_station)
    if stations_to_check:
        stations_to_check = stations_to_check.strip('[]').replace('"', '').split(',')
        stations_to_check = [station.strip() for station in stations_to_check]

    # 讀取雨量條件
    rainfall_condition = read_file(file_path_condition)

    try:
        # 發送 API 請求
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        #處理數據
        data = response.json()
        records = data.get('records', {}).get('Station', [])
        extracted_data = [
            {
                    '測站名稱': loc.get('StationName', 'N/A'),
                    '行政區': loc.get('GeoInfo', {}).get('TownName', 'N/A'),
                    '10分鐘': loc.get('RainfallElement', {}).get('Past10Min', {}).get('Precipitation', '0'),
                    '1小時': loc.get('RainfallElement', {}).get('Past1hr', {}).get('Precipitation', '0'),
                    '3小時': loc.get('RainfallElement', {}).get('Past3hr', {}).get('Precipitation', '0'),
                    '6小時': loc.get('RainfallElement', {}).get('Past6hr', {}).get('Precipitation', '0'),
                    '12小時': loc.get('RainfallElement', {}).get('Past12hr', {}).get('Precipitation', '0'),
                    '24小時': loc.get('RainfallElement', {}).get('Past24hr', {}).get('Precipitation', '0'),
                    '2天前': loc.get('RainfallElement', {}).get('Past2days', {}).get('Precipitation', '0'),
                    '資料時間': loc.get('ObsTime', {}).get('DateTime', 'N/A'),
                    '當前時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            for loc in records if loc.get('GeoInfo', {}).get('CountyName', '') == "新竹縣"
        ]

        # 創建 DataFrame
        if extracted_data:
            df = pd.DataFrame(extracted_data).replace('-', None)
            connection = pymysql.connect(
                host='localhost', user='root', password='1234567=',
                database='water_monitor', charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            # 檢查降雨量並發送通知
            line_notify_if_needed(stations_to_check, df, rainfall_condition, connection)

            # 插入數據到資料庫
            insert_data_to_db(df, connection)

            connection.commit()
            connection.close()

    except requests.RequestException as e:
        token = read_file(file_path_channel)
        messsage = f"Request error: {e}"
        send_error_notification(token,[messsage])
       
    except pymysql.MySQLError as e:
        token = read_file(file_path_channel)
        messsage = f"MySQL error: {e}"
        send_error_notification(token,[messsage])

    except Exception as e:
        token = read_file(file_path_lineapi)
        messsage = f"An unexpected error occurred: {e}"
        send_error_notification(token,[messsage])

# =========================
# 8. 設置定時任務
# =========================
schedule.every(1).minutes.do(fetch_and_store_data)

# =========================
# 9. 持續運行
# =========================
while True:
    schedule.run_pending()
    time.sleep(1)