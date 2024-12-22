
function addStation() {
    var stationSelect = document.getElementById('stationSelect');
    var stationName = stationSelect.value;

    // 創建一個新的測站項目
    var stationItem = document.createElement('div');
    stationItem.className = 'selected-station';
    stationItem.setAttribute('data-station', stationName);

    var stationText = document.createElement('span');
    stationText.textContent = stationName;

    var removeButton = document.createElement('button');
    removeButton.className = 'btn btn-danger btn-sm';
    removeButton.textContent = '移除';
    removeButton.setAttribute('type', 'button');
    removeButton.setAttribute('onclick', 'removeStation(this)');

    stationItem.appendChild(stationText);
    stationItem.appendChild(removeButton);

    // 將新項目添加到列表中
    var stationList = document.getElementById('stationList');
    stationList.appendChild(stationItem);
}

function removeStation(button) {
    // 移除測站項目
    var stationItem = button.parentElement;
    stationItem.remove();
}


function submitStations() {
    // 获取当前选择的测站列表
    var stationList = document.getElementById('stationList').children;
    var selectedStations = [];
    for (var i = 0; i < stationList.length; i++) {
        selectedStations.push(stationList[i].getAttribute('data-station'));
    }
    // 将选择的测站列表转为字符串
    var stationsString = JSON.stringify(selectedStations);
    // 提交数据到服务器
    $.ajax({
        url: '/save_selected_stations/',  // 替换为处理请求的 Django 视图 URL
        type: 'POST',
        data: {
            'selected_stations': stationsString,
            'csrfmiddlewaretoken': $('meta[name="csrf-token"]').attr('content')
        },
        xhrFields: {
            responseType: 'blob'  // 将响应类型设置为 Blob，以便处理文件下载
        },
        success: function (data, status, xhr) {
            alert("已提交選擇的測站");

            // 从响应中获取文件名
            var filename = xhr.getResponseHeader('Content-Disposition').split('filename=')[1];
            var blob = new Blob([data], { type: 'text/plain' });
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },
    });
}


function submitCondition() {
    var condition = document.getElementById('rainfallAmount').value;
    if (!isFloat(condition)) {
        alert('請輸入浮點數格式的降雨條件。');
        return;
    }
    // 禁用提交按钮，防止多次提交
    var submitButton = document.getElementById('submitBtn');
    // submitButton.disabled = true;
    $.ajax({
        url: '/save_rainfall_condition/',
        type: 'POST',
        data: {
            'rainfall_condition': condition,
        },
        success: function (data) {
            alert("已更新降雨條件");
            submitButton.disabled = false; // 提交成功后重新启用按钮
        }
    });
}

//提交群組金鑰
function submitAPIkey() {
    var APIkey = document.getElementById('APIkey').value;
    
    // 禁用提交按钮，防止多次提交
    var submitButton = document.getElementById('submitBtn');
    // submitButton.disabled = true;
    $.ajax({
        url: '/save_line_api/',
        type: 'POST',
        data: {
            'new_APIkey': APIkey,
        },
        success: function (data) {
            alert("已更新通知群組");
            submitButton.disabled = false; // 提交成功后重新启用按钮
        }
    });
}


// 檢查字串是否為浮點數
function isFloat(value) {
    var floatRegex = /^-?\d+(\.\d+)?$/;
    return floatRegex.test(value);
}


// 10/23 upgrade
// 閘門開度表單
function monitor_sheet_insert() {

    var close_date = document.getElementById('close_date').value;
    var close_time = document.getElementById('close_time').value;
    // 组合日期和时间
    var data_time = `${close_date} ${close_time}:00`;
    
    // 创建请求数据对象
    var formData = {
        'valve_close_time': data_time,
        'before_size': document.getElementById('open_size').value,
        'before_flow': document.getElementById('open_flow').value,
        'after_size': document.getElementById('close_size').value,
        'after_flow': document.getElementById('close_flow').value,
    };

    $.ajax({
        url: "/monitor_sheet_insert/",
        type: "POST",
        dataType: "json",
        data: formData,
        success: function (data) {
            alert(data['msg']);
            window.location.replace("/monitor_sheet/");
            console.log(data); // For debugging
        },
        error: function (xhr, status, error) {
            alert("AJAX Error: " + error);
        }
    });
}

// 10/23 upgrade 
// delete record
function deleteRecord(id) {
    if (confirm('確定要刪除此筆資料嗎？')) {
        $.ajax({
            url: '/delete_valve_record/',  // 後端處理刪除的 API
            type: 'POST',  // 使用 POST 方法
            data: { 'id': id },  // 傳遞要刪除的資料 ID
            success: function(data) {
                if (data.status === 'success') {
                    alert(data.msg);
                    // 刪除成功後重新載入頁面
                    location.reload();
                } else {
                    alert(`Error: ${data.msg}`);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                alert('發生錯誤，無法刪除資料');
            }
        });
    }
}

