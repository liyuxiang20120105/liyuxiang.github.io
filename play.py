from flask import Flask, request, render_template_string 
import json 
import os
from datetime import datetime
import socket 
 
app = Flask(__name__)
 
# 数据存储文件路径 
DATA_FILE = "danmu_data.json" 
 
# 初始化数据文件
if not os.path.exists(DATA_FILE): 
    with open(DATA_FILE, "w") as f:
        json.dump({"danmus":  [], "ips": {}}, f)
 
# 获取公网IP的函数 
def get_public_ip():
    try:
        return request.headers.get('X-Forwarded-For',  request.remote_addr) 
    except:
        return "Unknown"
 
# 赛博朋克像素风格网页模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>赛博像素弹幕空间</title>
    <style>
        body {
            background-color: #0a0a18;
            color: #0ff;
            font-family: 'Courier New', monospace;
            margin: 0;
            overflow: hidden;
            background-image: 
                radial-gradient(#ff00cc 1px, transparent 2px),
                radial-gradient(#00ffff 1px, transparent 2px);
            background-size: 50px 50px;
            background-position: 0 0, 25px 25px;
        }
        .container {
            position: relative;
            width: 100%;
            height: 100vh;
            border: 3px solid #ff00cc;
            box-shadow: 0 0 15px #00ffff, inset 0 0 15px #ff00cc;
        }
        .pixel-header {
            text-align: center;
            font-size: 32px;
            text-shadow: 0 0 10px #00ffff, 0 0 20px #ff00cc;
            margin: 20px 0;
            animation: glitch 3s infinite;
        }
        #danmu-container {
            position: relative;
            height: 70vh;
            overflow: hidden;
            border: 2px dashed #00ffff;
            margin: 15px;
        }
        .danmu {
            position: absolute;
            white-space: nowrap;
            font-size: 24px;
            text-shadow: 0 0 5px #fff, 0 0 10px #00ffff, 0 0 20px #ff00cc;
            color: #fff;
            animation: danmuMove linear;
        }
        .input-box {
            margin: 15px;
            text-align: center;
        }
        input {
            background: rgba(0, 0, 30, 0.8);
            color: #00ffff;
            border: 2px solid #ff00cc;
            padding: 10px;
            width: 70%;
            font-size: 18px;
            outline: none;
        }
        button {
            background: #ff00cc;
            color: #000;
            border: none;
            padding: 10px 20px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            margin-left: 10px;
        }
        button:hover {
            background: #00ffff;
            box-shadow: 0 0 15px #00ffff;
        }
        .admin-link {
            position: absolute;
            bottom: 10px;
            right: 10px;
            color: #ff00cc;
            text-decoration: none;
        }
        @keyframes danmuMove {
            from { transform: translateX(100vw); }
            to { transform: translateX(-100%); }
        }
        @keyframes glitch {
            0% { transform: translate(0); }
            20% { transform: translate(-5px, 5px); }
            40% { transform: translate(-5px, -5px); }
            60% { transform: translate(5px, 5px); }
            80% { transform: translate(5px, -5px); }
            100% { transform: translate(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="pixel-header">赛博像素弹幕空间</h1>
        <div id="danmu-container"></div>
        
        <div class="input-box">
            <input type="text" id="danmu-input" placeholder="输入你的弹幕 (按Enter发送)" maxlength="50">
            <button onclick="sendDanmu()">发送</button>
        </div>
        
        <a href="/admin" class="admin-link">管理后台</a>
    </div>
 
    <script>
        let danmuSpeed = 10; // 弹幕速度系数 
        
        // 初始化加载历史弹幕 
        fetch('/get_danmu')
            .then(response => response.json()) 
            .then(data => {
                data.forEach(danmu  => {
                    createDanmu(danmu.content); 
                });
            });
        
        // 创建弹幕元素 
        function createDanmu(text) {
            const container = document.getElementById('danmu-container'); 
            const danmu = document.createElement('div'); 
            danmu.className  = 'danmu';
            danmu.textContent  = text;
            
            // 随机位置和样式 
            const top = Math.floor(Math.random()  * 80);
            danmu.style.top  = `${top}%`;
            danmu.style.animationDuration  = `${Math.random()  * 10 + 10}s`;
            danmu.style.color  = getRandomColor();
            
            container.appendChild(danmu); 
            
            // 动画结束后移除元素
            setTimeout(() => {
                danmu.remove(); 
            }, parseFloat(danmu.style.animationDuration)  * 1000);
        }
        
        // 发送弹幕 
        function sendDanmu() {
            const input = document.getElementById('danmu-input'); 
            const content = input.value.trim(); 
            
            if (content) {
                // 发送到服务器 
                fetch('/send_danmu', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({  content: content })
                });
                
                // 立即显示 
                createDanmu(content);
                input.value  = '';
            }
        }
        
        // 随机霓虹色 
        function getRandomColor() {
            const colors = [
                '#ff00cc', '#00ffff', '#00ff00', '#ffff00', '#ff6600'
            ];
            return colors[Math.floor(Math.random() * colors.length)]; 
        }
        
        // 监听Enter键 
        document.getElementById('danmu-input').addEventListener('keypress',  (e) => {
            if (e.key  === 'Enter') {
                sendDanmu();
            }
        });
    </script>
</body>
</html>
'''
 
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>访问者信息 - 赛博空间</title>
    <style>
        body {
            background-color: #0d0d20;
            color: #0ff;
            font-family: 'Courier New', monospace;
            margin: 30px;
        }
        h1 {
            color: #ff00cc;
            text-shadow: 0 0 10px #ff00cc;
            border-bottom: 2px solid #00ffff;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #00ffff;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #005555;
            color: #00ffff;
        }
        tr:nth-child(even) {
            background-color: #0a1530;
        }
        .glitch-text {
            animation: glitch 1s infinite;
        }
        @keyframes glitch {
            0% { text-shadow: 2px 0 0 #ff00cc; }
            50% { text-shadow: -2px 0 0 #00ffff; }
            100% { text-shadow: 2px 0 0 #ff00cc; }
        }
    </style>
</head>
<body>
    <h1 class="glitch-text">访问者追踪面板</h1>
    <table>
        <thead>
            <tr>
                <th>IP地址</th>
                <th>地理位置</th>
                <th>访问次数</th>
                <th>首次访问</th>
                <th>最近访问</th>
            </tr>
        </thead>
        <tbody>
            {% for ip, data in ip_data.items()  %}
            <tr>
                <td>{{ ip }}</td>
                <td>{% if ip != 'Unknown' %}ISP:{{ data.isp |default('未知') }}{% else %}未知{% endif %}</td>
                <td>{{ data.count  }}</td>
                <td>{{ data.first_seen  }}</td>
                <td>{{ data.last_seen  }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''
 
@app.route('/') 
def index():
    ip = get_public_ip()
    update_ip_record(ip)
    return render_template_string(HTML_TEMPLATE)
 
@app.route('/send_danmu',  methods=['POST'])
def send_danmu():
    content = request.json.get('content',  '')
    ip = get_public_ip()
    
    if content:
        with open(DATA_FILE, 'r+') as f:
            data = json.load(f) 
            data['danmus'].append({
                "content": content,
                "time": datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
                "ip": ip 
            })
            f.seek(0) 
            json.dump(data,  f, indent=2)
            f.truncate() 
            
            update_ip_record(ip)
    
    return {"status": "success"}
 
@app.route('/get_danmu') 
def get_danmu():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f) 
        return {"danmus": [d['content'] for d in data['danmus'][-50:]]}
 
@app.route('/admin') 
def admin():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f) 
        return render_template_string(ADMIN_TEMPLATE, ip_data=data['ips'])
 
def update_ip_record(ip):
    with open(DATA_FILE, 'r+') as f:
        data = json.load(f) 
        ips = data.get('ips',  {})
        
        if ip not in ips:
            try:
                # 简化的地理位置查询 (实际项目中应使用专业API)
                hostname = socket.gethostbyaddr(ip)[0]()  if ip != 'Unknown' else 'Unknown'
                isp = "ISP:" + hostname.split('.')[-1].upper()  if '.' in hostname else 'Unknown'
            except:
                isp = "Unknown"
                
            ips[ip] = {
                "count": 1,
                "first_seen": datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
                "last_seen": datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
                "isp": isp
            }
        else:
            ips[ip]['count'] += 1 
            ips[ip]['last_seen'] = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        
        data['ips'] = ips
        f.seek(0) 
        json.dump(data,  f, indent=2)
        f.truncate() 
 
if __name__ == '__main__':
    app.run(host='0.0.0.0',  port=5432, debug=True)