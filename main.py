"""
🚀 Nexus Extractor - WEB DASHBOARD & API GATEWAY
"""
import os, json, secrets, time, threading
from datetime import datetime
from io import BytesIO
from flask import Flask, request, jsonify, render_template_string, send_file, session, redirect, url_for
import redis

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

REDIS_URL = os.environ.get("REDIS_URL", "redis://default:fuHrGqESMbVVRciLtcxCzsKaeUdGnrOU@interchange.proxy.rlwy.net:58097")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://your-domain.com").rstrip('/')
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")
APP_SECRET_HEADER = "JetApp-Secure-Client"

db = redis.Redis.from_url(REDIS_URL, decode_responses=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>پنل مدیریت Nexus</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; font-family: Tahoma, Arial; font-size: 14px;}
        .log-console { background: #1e1e1e; color: #00ff00; height: 350px; overflow-y: scroll; padding: 15px; font-family: Consolas, monospace; border-radius: 6px; font-size: 13px;}
        .table-wrapper { height: 350px; overflow-y: auto; }
    </style>
</head>
<body>
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
        <h4 class="m-0">⚙️ کنترل پنل Nexus</h4>
        <a href="/logout" class="btn btn-danger btn-sm">خروج از اکانت</a>
    </div>
    
    <div class="row">
        <div class="col-md-3 mb-3">
            <div class="card shadow-sm border-0">
                <div class="card-body">
                    <h6 class="card-title text-muted mb-3">دستورات سرور</h6>
                    <button onclick="sendCommand('START_BULK')" class="btn btn-primary w-100 mb-2">▶️ استارت پردازش گروهی</button>
                    <a href="/export/links" class="btn btn-outline-success w-100 mb-2">🔗 دانلود فایل لینک‌ها</a>
                    <a href="/export/json" class="btn btn-outline-secondary w-100 mb-4">📦 بکاپ دیتابیس (JSON)</a>
                    <hr>
                    <button onclick="if(confirm('کل دیتابیس فلش شود؟ این عملیات غیرقابل بازگشت است.')) sendCommand('CLEAR_DB')" class="btn btn-danger w-100">🧹 فلش کردن کل دیتابیس</button>
                </div>
            </div>
        </div>
        
        <div class="col-md-9">
            <ul class="nav nav-tabs" id="myTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="logs-tab" data-bs-toggle="tab" data-bs-target="#logs" type="button" role="tab">مانیتورینگ لوکال</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="db-tab" data-bs-toggle="tab" data-bs-target="#db" type="button" role="tab" onclick="fetchAccounts()">مدیریت لینک‌ها</button>
                </li>
            </ul>
            
            <div class="tab-content border border-top-0 bg-white p-3 shadow-sm" id="myTabContent">
                <!-- Logs Tab -->
                <div class="tab-pane fade show active" id="logs" role="tabpanel">
                    <div class="d-flex justify-content-between mb-2">
                        <small class="text-muted">ارتباط زنده با کلاینت لوکال...</small>
                        <button onclick="fetchLogs()" class="btn btn-sm btn-light border">🔄 رفرش</button>
                    </div>
                    <div id="logViewer" class="log-console">منتظر دریافت دیتای لوکال...</div>
                </div>
                
                <!-- DB Tab -->
                <div class="tab-pane fade" id="db" role="tabpanel">
                    <div class="d-flex justify-content-between mb-2">
                        <small class="text-muted" id="accCount">تعداد اکانت‌ها: 0</small>
                        <button onclick="fetchAccounts()" class="btn btn-sm btn-light border">🔄 رفرش جدول</button>
                    </div>
                    <div class="table-wrapper">
                        <table class="table table-hover table-sm border">
                            <thead class="table-light sticky-top">
                                <tr>
                                    <th>شماره خط</th>
                                    <th>نام پروفایل</th>
                                    <th>لینک ورود</th>
                                    <th>عملیات</th>
                                </tr>
                            </thead>
                            <tbody id="accTableBody">
                                <tr><td colspan="4" class="text-center text-muted">دیتایی یافت نشد</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    function sendCommand(cmd) {
        fetch('/api/command', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: cmd})
        }).then(res => res.json()).then(data => alert(data.message));
    }

    function fetchLogs() {
        fetch('/api/logs').then(res => res.json()).then(data => {
            const box = document.getElementById('logViewer');
            box.innerHTML = data.logs.length ? data.logs.join('<br>================<br>') : 'لاگ جدیدی در صف نیست.';
            box.scrollTop = box.scrollHeight;
        });
    }

    function fetchAccounts() {
        fetch('/api/accounts').then(res => res.json()).then(data => {
            document.getElementById('accCount').innerText = `تعداد اکانت‌ها: ${data.length}`;
            const tbody = document.getElementById('accTableBody');
            tbody.innerHTML = '';
            if(data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">جدول خالی است</td></tr>';
                return;
            }
            data.forEach(acc => {
                let tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${acc.phone}</td>
                    <td>${acc.name}</td>
                    <td><input type="text" class="form-control form-control-sm" value="${acc.link}" readonly></td>
                    <td><button onclick="deleteAcc('${acc.phone}')" class="btn btn-sm btn-outline-danger">حذف</button></td>
                `;
                tbody.appendChild(tr);
            });
        });
    }

    function deleteAcc(phone) {
        if(!confirm(`اکانت ${phone} حذف شود؟ (خط آزاد می‌شود)`)) return;
        fetch('/api/accounts/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phone: phone})
        }).then(res => res.json()).then(data => {
            fetchAccounts();
        });
    }

    setInterval(() => {
        if(document.getElementById('logs-tab').classList.contains('active')) fetchLogs();
    }, 4000);
    fetchLogs();
</script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8"><title>ورود</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center justify-content-center" style="height: 100vh;">
    <div class="card shadow-sm p-4" style="width: 320px;">
        <h5 class="text-center mb-4">ورود به ادمین</h5>
        <form method="POST" action="/login">
            <input type="password" name="password" class="form-control mb-3" placeholder="پسورد..." required>
            <button type="submit" class="btn btn-dark w-100">لاگین</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return render_template_string(LOGIN_TEMPLATE)
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return "پسورد اشتباه است", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))

@app.route('/api/command', methods=['POST'])
def api_command():
    if not session.get('logged_in'): return jsonify({"message": "دسترسی غیرمجاز"}), 401
    cmd = request.json.get('command')
    if cmd == "START_BULK":
        db.rpush("bot:admin_commands", "START_BULK")
        return jsonify({"message": "فرمان استارت به کلاینت لوکال ارسال شد."})
    elif cmd == "CLEAR_DB":
        db.delete("jet:processed_phones")
        db.delete("jet:bulk_accounts")
        return jsonify({"message": "دیتابیس به طور کامل فلش شد."})
    return jsonify({"message": "دستور نامعتبر"}), 400

@app.route('/api/logs')
def api_logs():
    if not session.get('logged_in'): return jsonify({"logs": []}), 401
    logs = db.lrange("bot:admin_alerts", -15, -1)
    return jsonify({"logs": logs})

@app.route('/api/accounts')
def api_accounts():
    if not session.get('logged_in'): return jsonify([]), 401
    records = db.hgetall("jet:bulk_accounts")
    result = []
    for phone, val in records.items():
        data = json.loads(val)
        result.append({
            "phone": phone,
            "name": data['name'],
            "link": f"{WEBHOOK_URL}/auth/{data['token']}"
        })
    return jsonify(result)

@app.route('/api/accounts/delete', methods=['POST'])
def delete_account():
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    phone = request.json.get('phone')
    record = db.hget("jet:bulk_accounts", phone)
    if record:
        data = json.loads(record)
        db.delete(f"jet_session:{data['token']}") # پاک کردن سشن
        db.hdel("jet:bulk_accounts", phone) # پاک کردن از لیست
        db.srem("jet:processed_phones", phone) # آزاد کردن خط برای استارت مجدد
    return jsonify({"status": "ok"})

@app.route('/export/links')
def export_links():
    if not session.get('logged_in'): return "دسترسی غیرمجاز", 401
    records = db.hgetall("jet:bulk_accounts")
    text = "لیست لینک‌های استخراج شده:\n\n"
    for phone, val in records.items():
        data = json.loads(val)
        text += f"Phone: {phone}\nName: {data['name']}\nLink: {WEBHOOK_URL}/auth/{data['token']}\n--------------------\n"
    return send_file(BytesIO(text.encode('utf-8')), as_attachment=True, download_name=f"Links_{datetime.now().strftime('%Y%m%d')}.txt", mimetype='text/plain')

@app.route('/export/json')
def export_json():
    if not session.get('logged_in'): return "دسترسی غیرمجاز", 401
    keys = db.keys("jet_session:*")
    accs = {k: json.loads(db.get(k)) for k in keys if db.get(k)}
    return send_file(BytesIO(json.dumps(accs, ensure_ascii=False, indent=2).encode('utf-8')), as_attachment=True, download_name=f"Backup_{datetime.now().strftime('%Y%m%d')}.json", mimetype='application/json')

@app.route('/auth/<token>')
def secure_gateway(token):
    session_str = db.get(f"jet_session:{token}")
    if not session_str:
        return "لینک نامعتبر یا منقضی شده است.", 404
    u_agent = request.headers.get("User-Agent", "")
    app_hdr = request.headers.get("X-Client-App", "")
    if app_hdr == APP_SECRET_HEADER or "JetAppClient" in u_agent:
        return jsonify({"status": "success", "session": json.loads(session_str)})
    return '<html dir="rtl"><body style="font-family:Tahoma;text-align:center;margin-top:50px;">دسترسی غیرمجاز. لینک فقط در اپ باز می‌شود.</body></html>'

def token_worker():
    while True:
        try:
            raw = db.lpop("bot:new_accounts")
            if raw:
                acc = json.loads(raw)
                tkn = secrets.token_urlsafe(14)
                db.setex(f"jet_session:{tkn}", 30 * 24 * 3600, json.dumps(acc["data"], ensure_ascii=False))
                db.hset("jet:bulk_accounts", acc["phone"], json.dumps({"phone": acc["phone"], "token": tkn, "name": acc["name"]}, ensure_ascii=False))
        except: pass
        time.sleep(1)

threading.Thread(target=token_worker, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
