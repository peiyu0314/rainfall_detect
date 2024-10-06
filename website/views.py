from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django import template
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
import pymysql
import pymysql.cursors
from django.shortcuts import render
from datetime import datetime
import sys
import traceback
import os
from django.conf import settings
from datetime import datetime, timedelta

# cd /Users/dengpeiyu/Desktop/上水汙水處理/rainfall_dect
# python manage.py runserver
# git init


# 主頁
@csrf_protect
def monitor_table(request):
    result = {'status': 'success', 'msg': '', 'data': []}
    latest_data = None
    try:
        connection = pymysql.connect(
            host='localhost', port=3306, user='root', password='1234567=', database='water monitor', charset='utf8mb4')
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        # SQL 查询该时间点的所有降雨数据
        sql = """
        SELECT * FROM `rainfall_web`
        WHERE `data_time` = (SELECT MAX(`data_time`) FROM `rainfall_web`) ORDER BY `rainfall_10min` DESC;
        """
        
        cursor.execute(sql)
        latest_data = cursor.fetchall()  # 获取该时间点的所有数据

        if latest_data:
            result['data'] = latest_data
            result['msg'] = f'成功取得最近 {data_time} 的降雨資料'
            print(result['msg'])
        else:
            result['msg'] = '沒有符合條件的降雨資料'
            print(result['msg'])

    except Exception as e:
        result['status'] = 'error'
        error_class = e.__class__.__name__  # 获取错误类型
        detail = e.args[0]  # 获取详细内容
        cl, exc, tb = sys.exc_info()  # 获取Call Stack
        lastCallStack = traceback.extract_tb(tb)[-1]  # 获取Call Stack的最后一条数据
        fileName = lastCallStack.filename  # 获取发生的文件名称
        lineNum = lastCallStack.lineno  # 获取发生的行号
        funcName = lastCallStack.name  # 获取发生的函数名称
        errMsg = f"File \"{fileName}\", line {lineNum}, in {funcName}: [{error_class}] {detail}"
        result['msg'] = errMsg

    

    # 传递数据时间到模板
    data_time = latest_data[0]['data_time'].strftime('%Y-%m-%d %H:%M:%S') if latest_data else None

    file_path_station = os.path.join(settings.BASE_DIR, 'static/media', 'stations.txt')
    
    # Read the stations from the file
    if os.path.exists(file_path_station):
        with open(file_path_station, 'r') as file:
            stations_to_check = file.read().strip('[]').replace('"', '').split(',')
    stations_string = ', '.join([station.strip() for station in stations_to_check])

     # Read the rainfall condition from the file
    file_path_condition = os.path.join(settings.BASE_DIR, 'static/media', 'condition.txt')
    if os.path.exists(file_path_condition):
        with open(file_path_condition, 'r') as file:
             rainfall = file.read()
    
    # read record_station frme the file
    file_path_record = os.path.join(settings.BASE_DIR, 'static/media', 'record_notified_station.txt')
    if os.path.exists(file_path_record):
        with open(file_path_record, 'r') as file:
             record = file.read()
           

    context = {
        'rainfall_data': result['data'],
        'data_time': data_time,
        'stations_string': stations_string,
        'rainfall':rainfall,
        'record':record,
    }
    response = render(request, 'monitor_table.html', context)
    response['Strict-Transport-Security'] = 'max-age=2592000'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-XSS-Protection'] = '1; mode=block'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Strict-Transport-Security'] = 'max-age=16070400; includeSubDomains'
    
    return response


# 選擇觀測測站
def select_station(request):
    file_path = os.path.join(settings.BASE_DIR, 'static/media', 'stations.txt')
    
    # Initialize the station list
    stations_list = []
    
    # Read the stations from the file
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()
            stations_list = [station.strip().strip('[]').strip('"').strip("'") for station in content.split(',')]
    
    stations_list = [station for station in stations_list]

    context = {'stations_to_check': stations_list}
    
    response = render(request, 'select_station.html', context)
    
    # Security headers
    response['Strict-Transport-Security'] = 'max-age=2592000'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-XSS-Protection'] = '1; mode=block'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Strict-Transport-Security'] = 'max-age=16070400; includeSubDomains'
    
    return response

#儲存選擇的測站
@csrf_exempt
def save_selected_stations(request):
    if request.method == 'POST':
        # 获取传入的测站列表
        selected_stations = request.POST.get('selected_stations', '')
        # 将测站列表分割成数组
        stations_list = selected_stations.split(',')
        # 创建一个字符串，包含所有测站
        txt_content = ",".join(stations_list)
        # 使用相对路径保存文件，路径相对于 Django 项目的根目录
        file_dir = os.path.join(settings.BASE_DIR, 'static/media')
        file_name = 'stations.txt'
        file_path = os.path.join(file_dir, file_name)
        # 将内容写入文件
        with open(file_path, 'w') as file:
            file.write(txt_content)
        # 返回一个简单的响应确认保存成功
        return HttpResponse(f"File saved successfully at: {file_path}")


# 變更雨量條件
@csrf_protect
def notify_condition(request):
    file_path = os.path.join(settings.BASE_DIR, 'static/media', 'condition.txt')
    # Read the stations from the file
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
           
    context = {'rainfall': content}
    
    response = render(request, 'notify_condition.html', context)
    response['Strict-Transport-Security'] = 'max-age=2592000'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-XSS-Protection'] = '1; mode=block'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Strict-Transport-Security'] = 'max-age=16070400; includeSubDomains'
    return response


#儲存雨量條件
@csrf_exempt
def save_rainfall_condition(request):
    if request.method == 'POST':
        condition = request.POST.get('rainfall_condition')

        # 使用相对路径保存文件，路径相对于 Django 项目的根目录
        file_dir = os.path.join(settings.BASE_DIR, 'static/media')
        file_name = 'condition.txt'
        file_path = os.path.join(file_dir, file_name)

        # 将内容写入文件
        with open(file_path, 'w') as file:
            file.write(condition)
        # 返回一个简单的响应确认保存成功
        return HttpResponse(f"File saved successfully at: {file_path}")


# 閘門開度table
@csrf_protect
def valve_table(request):
    result = {'status':'success', 'msg':'', 'data':[]}
    latest_data = None
    try:
        connection = pymysql.connect(host='localhost', port=3306, user='root', password='1234567=', database='water monitor', charset='utf8mb4')
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        sql = """SELECT * FROM `valve_table`
         ORDER BY `valve_close_time` DESC """
        cursor.execute(sql)
        latest_data = cursor.fetchall()

        # 遍历查询结果，修改时间格式
        for index, data in enumerate(latest_data):
            if isinstance(latest_data[index]['valve_close_time'], str):
                latest_data[index]['valve_close_time'] = datetime.strptime(latest_data[index]['valve_close_time'], '%Y-%m-%d %H:%M:%S')
            if isinstance(latest_data[index]['current_time'], str):
                latest_data[index]['current_time'] = datetime.strptime(latest_data[index]['current_time'], '%Y-%m-%d %H:%M:%S')
            # 修改时间的显示格式
            latest_data[index]['valve_close_time'] = latest_data[index]['valve_close_time'].strftime('%Y-%m-%d %H:%M:%S')
            latest_data[index]['current_time'] = latest_data[index]['current_time'].strftime('%Y-%m-%d %H:%M:%S')

       
        if latest_data:
            result['data'] = latest_data
            result['msg'] = f'成功取得閘門資料'
            print(result['msg'])
        else:
            result['msg'] = '無法取得資料'
            print(result['msg'])
           
    except Exception as e:
        result['status'] = 'error'
        error_class = e.__class__.__name__  # 获取错误类型
        detail = e.args[0]  # 获取详细内容
        cl, exc, tb = sys.exc_info()  # 获取Call Stack
        lastCallStack = traceback.extract_tb(tb)[-1]  # 获取Call Stack的最后一条数据
        fileName = lastCallStack.filename  # 获取发生的文件名称
        lineNum = lastCallStack.lineno  # 获取发生的行号
        funcName = lastCallStack.name  # 获取发生的函数名称
        errMsg = f"File \"{fileName}\", line {lineNum}, in {funcName}: [{error_class}] {detail}"
        result['msg'] = errMsg

    finally:
        connection.close()
    
    context = {
             'valve_data':result['data']
        }

    response = render(request,'valve_table.html',context)
    response['Strict-Transport-Security'] = 'max-age=2592000'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-XSS-Protection'] = '1; mode=block'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Strict-Transport-Security'] = 'max-age=16070400; includeSubDomains'
    return response



# 閘門開度表單
@csrf_protect
def monitor_sheet(request):
	response = render(request,'monitor_sheet.html',{})
	response['Strict-Transport-Security'] = 'max-age=2592000'
	response['X-Frame-Options'] = 'SAMEORIGIN'
	response['Referrer-Policy'] = 'no-referrer'
	response['X-XSS-Protection'] = '1; mode=block'
	response['X-Content-Type-Options'] = 'nosniff'
	response['Strict-Transport-Security'] = 'max-age=16070400; includeSubDomains'
	return response


# 新增一筆閘門資料
@csrf_exempt
def monitor_sheet_insert(request):
	result = {'status': 'success', 'msg': '', 'data': {}}
	fields = ['valve_close_time', 'before_size', 'before_flow', 'after_size', 'after_flow', 'current_time']
	sheet_data = request.POST.copy()  # 创建POST数据的副本
	sheet_data['current_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	try:
		connection = pymysql.connect(
			host='localhost', port=3306, user='root', password='1234567=', database='water monitor', charset='utf8mb4')
		cursor = connection.cursor(pymysql.cursors.DictCursor)
		# create SQL statement
		
		sql = f"INSERT INTO `monitor_sheet` ({', '.join([f'`{field}`' for field in fields])}) VALUES ({', '.join(['%s'] * len(fields))});"
		values = [sheet_data[field] for field in fields]
		
		cursor.execute(sql, values)
		connection.commit()
		result['msg'] = '成功新增一筆資料'

	except Exception as e:
		result['status'] = '請確認必填欄位與其名稱是否重複'
		error_class = e.__class__.__name__  # 取得錯誤類型
		detail = e.args[0]  # 取得詳細內容
		cl, exc, tb = sys.exc_info()  # 取得Call Stack
		lastCallStack = traceback.extract_tb(tb)[-1]  # 取得Call Stack的最後一筆資料
		fileName = lastCallStack.filename  # 取得發生的檔案名稱
		lineNum = lastCallStack.lineno  # 取得發生的行號
		funcName = lastCallStack.name  # 取得發生的函數名稱
		errMsg = f"File \"{fileName}\", line {lineNum}, in {funcName}: [{error_class}] {detail}"
		result['msg'] = errMsg

	return JsonResponse(result, safe=False)



# 變更line group
@csrf_protect
def notify_line(request):
    file_path = os.path.join(settings.BASE_DIR, 'static/media', 'APIkey.txt')
    # Read the stations from the file
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
           
    context = {'APIkey': content}
    
    response = render(request, 'notify_line.html', context)
    response['Strict-Transport-Security'] = 'max-age=2592000'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Referrer-Policy'] = 'no-referrer'
    response['X-XSS-Protection'] = '1; mode=block'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Strict-Transport-Security'] = 'max-age=16070400; includeSubDomains'
    return response


#儲存apikey
@csrf_exempt
def save_line_api(request):
    if request.method == 'POST':
        apikey = request.POST.get('new_APIkey')

        # 使用相对路径保存文件，路径相对于 Django 项目的根目录
        file_dir = os.path.join(settings.BASE_DIR, 'static/media')
        file_name = 'APIkey.txt'
        file_path = os.path.join(file_dir, file_name)

        # 将内容写入文件
        with open(file_path, 'w') as file:
            file.write(apikey)
        # 返回一个简单的响应确认保存成功
        return HttpResponse(f"File saved successfully at: {file_path}")


	


