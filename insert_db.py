import pandas as pd
import pymysql
from datetime import datetime

# 使用 pandas 读取 Excel 文件
df = pd.read_excel('valve_response.xlsx')

# 合并日期和阀门关闭时间为一个时间戳
df['timestamp'] = pd.to_datetime(df['時間戳記'].astype(str) + ' ' + df['閘門關閉時間(有上午下午之分)'].astype(str))
df['current_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print(df)

# 连接MySQL
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='1234567=',  # 改为您的密码
    database='water_monitor',  # 改为您的数据库名称
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        # 插入数据
        sql_insert = """
        INSERT INTO `valve_table` 
        (`valve_close_time`, `before_size`, `before_flow`, `after_size`, `after_flow`, `current_time`)
        VALUES (%s, %s, %s, %s, %s,%s)
        """
        
        # 遍历 DataFrame 中的每一行，插入到数据库中
        for index, row in df.iterrows():
            cursor.execute(sql_insert, (
                row['timestamp'],  # 替换为 Excel 文件中的列名
                row['閘門關閉前開度'],
                row['閘門關閉前瞬間流量'],
                row['閘門關閉後開度'],
                row['閘門關閉後瞬間流量'],
                row['current_time']
            ))
        connection.commit()

finally:
    connection.close()