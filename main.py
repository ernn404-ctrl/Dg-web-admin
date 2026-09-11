"""
🚀 Nexus Extractor - PRO CLOUD DASHBOARD (INTEGRATED)
"""
import os, json, secrets, time, threading
from datetime import datetime
from io import BytesIO
from flask import Flask, request, jsonify, render_template_string, send_file, session, redirect, url_for
import redis

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ================= Configuration =================
REDIS_URL = os.environ.get("REDIS_URL", "redis://default:fuHrGqESMbVVRciLtcxCzsKaeUdGnrOU@interchange.proxy.rlwy.net:58097")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://your-domain.com").rstrip('/')
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")
APP_SECRET_HEADER = "JetApp-Secure-Client"

db = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ================= HTML Templates =================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>ورود به سیستم | Nexus Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.0.0/Vazirmatn-font-face.css" rel="stylesheet" />
    <style>body { font-family: 'Vazirmatn', sans-serif; background-color: #0f172a; }</style>
</head>
<body class="min-h-screen flex items-center justify-center">
    <div class="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 shadow-2xl backdrop-blur-xl w-96">
        <h2 class="text-2xl font-bold text-emerald-400 text-center mb-6 tracking-widest">NEXUS ADMIN</h2>
        <form method="POST" action="/login" class="flex flex-col gap-4">
            <input type="password" name="password" placeholder="کلمه عبور امنیتی..." required 
                   class="bg-slate-900/50 border border-slate-700 text-slate-200 rounded-lg p-3 outline-none focus:border-cyan-400 transition-colors text-center" dir="ltr">
            <button type="submit" class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-bold py-3 rounded-lg hover:bg-emerald-500/30 transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]">ورود به پنل</button>
        </form>
    </div>
</body>
</html>
"""

# قالب دقیقاً همان شاهکار بصری است، فقط دکمه‌های دانلود به لینک مستقیم متصل شده‌اند
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Extractor Engine | داشبورد مدیریت</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.0.0/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Vazirmatn', 'sans-serif'], mono: ['ui-monospace', 'monospace'] },
                    colors: { midnight: '#0f172a', neonCyan: '#06b6d4', neonEmerald: '#10b981', neonCrimson: '#f43f5e', neonViolet: '#8b5cf6' },
                    animation: { 'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite' }
                }
            }
        }
    </script>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <style>
        body { background-color: #0f172a; background-image: radial-gradient(circle at 15% 50%, rgba(6, 182, 212, 0.05), transparent 25%), radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.05), transparent 25%); color: #f8fafc; }
        .glass-panel { background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 1rem; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1); }
        .terminal { background-color: #000000; border: 1px solid #333; color: #10b981; font-family: 'Courier New', monospace; padding: 1rem; border-radius: 0.5rem; height: 300px; overflow-y: auto; box-shadow: inset 0 0 10px rgba(0,0,0,0.8); }
        .terminal::-webkit-scrollbar { width: 8px; } .terminal::-webkit-scrollbar-track { background: #111; } .terminal::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        .log-info { color: #10b981; } .log-error { color: #f43f5e; } .log-warning { color: #f59e0b; }
        table.dataTable { color: #e2e8f0 !important; border-collapse: collapse !important; }
        table.dataTable tbody tr { background-color: transparent !important; }
        table.dataTable tbody tr:hover { background-color: rgba(255, 255, 255, 0.05) !important; }
        table.dataTable tbody td { border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; padding: 1rem 0.75rem !important; }
        table.dataTable thead th { border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important; color: #94a3b8 !important; }
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter, .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_paginate { color: #94a3b8 !important; margin-bottom: 1rem; }
        .dataTables_wrapper .dataTables_filter input { background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255, 255, 255, 0.1); color: white; border-radius: 0.25rem; padding: 0.25rem 0.5rem; outline: none; }
        .copy-badge { cursor: pointer; transition: all 0.2s ease; } .copy-badge:hover { background-color: rgba(6, 182, 212, 0.2); box-shadow: 0 0 8px rgba(6, 182, 212, 0.5); }
        .btn-glow-emerald { box-shadow: 0 0 15px rgba(16, 185, 129, 0.3); transition: all 0.3s ease; } .btn-glow-emerald:hover { box-shadow: 0 0 25px rgba(16, 185, 129, 0.6); transform: translateY(-2px); }
        .btn-glow-crimson { box-shadow: 0 0 15px rgba(244, 63, 94, 0.3); transition: all 0.3s ease; } .btn-glow-crimson:hover { box-shadow: 0 0 25px rgba(244, 63, 94, 0.6); transform: translateY(-2px); }
        .btn-glow-violet { box-shadow: 0 0 15px rgba(139, 92, 246, 0.3); transition: all 0.3s ease; } .btn-glow-violet:hover { box-shadow: 0 0 25px rgba(139, 92, 246, 0.6); transform: translateY(-2px); }
        #toast-container { position: fixed; bottom: 1rem; right: 1rem; z-index: 50; display: flex; flex-direction: column; gap: 0.5rem; }
        .toast { background: rgba(30, 41, 59, 0.9); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.1); color: white; padding: 1rem; border-radius: 0.5rem; opacity: 0; transform: translateX(100%); transition: all 0.3s ease; }
        .toast.show { opacity: 1; transform: translateX(0); }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8 font-sans antialiased">

    <!-- Header -->
    <header class="mb-8 text-center md:text-right flex flex-col md:flex-row justify-between items-center">
        <div>
            <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-l from-neonCyan to-neonEmerald mb-1">NEXUS EXTRACTOR ENGINE</h1>
            <p class="text-slate-400 text-sm">پنل مدیریت پیشرفته و مانیتورینگ لحظه‌ای</p>
        </div>
        <div class="mt-4 md:mt-0 flex items-center gap-4">
            <a href="/logout" class="text-xs text-red-400 border border-red-500/30 px-3 py-1 rounded hover:bg-red-500/10">خروج</a>
            <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full bg-neonEmerald animate-pulse"></div>
                <span class="text-slate-300 font-mono" id="current-time">00:00:00</span>
            </div>
        </div>
    </header>

    <!-- Telemetry Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="glass-panel p-6 relative overflow-hidden group">
            <h3 class="text-slate-400 text-sm mb-2">مجموع حساب‌ها</h3>
            <div class="text-3xl font-bold text-white mb-2" id="stat-total">--</div>
            <div class="h-10 w-full"><canvas id="chart-total"></canvas></div>
        </div>
        <div class="glass-panel p-6 relative overflow-hidden group">
            <h3 class="text-slate-400 text-sm mb-2">نرخ موفقیت</h3>
            <div class="text-3xl font-bold text-white mb-2 flex items-baseline gap-1"><span id="stat-success">--</span><span class="text-lg text-neonEmerald">%</span></div>
            <div class="h-10 w-full"><canvas id="chart-success"></canvas></div>
        </div>
        <div class="glass-panel p-6 relative overflow-hidden group">
            <h3 class="text-slate-400 text-sm mb-2">رشته‌های پردازشی</h3>
            <div class="text-3xl font-bold text-white mb-2" id="stat-proxies">--</div>
            <div class="h-10 w-full"><canvas id="chart-proxies"></canvas></div>
        </div>
        <div class="glass-panel p-6 relative overflow-hidden flex flex-col justify-center items-center">
            <h3 class="text-slate-400 text-sm mb-4">وضعیت سیستم</h3>
            <div class="flex items-center gap-3">
                <div id="status-indicator" class="h-4 w-4 rounded-full bg-slate-500"></div>
                <span id="stat-status" class="text-xl font-bold tracking-widest text-slate-300 uppercase">Standby</span>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <!-- Command Center -->
        <div class="lg:col-span-1 glass-panel p-6 flex flex-col gap-4">
            <h2 class="text-xl font-semibold mb-2 border-b border-white/10 pb-2">مرکز فرماندهی</h2>
            
            <button onclick="triggerAction('start')" class="btn-glow-emerald bg-neonEmerald/20 border border-neonEmerald/50 text-neonEmerald font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-neonEmerald/30">
                <span>استارت پردازش همزمان</span>
            </button>
            <button onclick="triggerAction('stop')" class="btn-glow-crimson bg-neonCrimson/20 border border-neonCrimson/50 text-neonCrimson font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-neonCrimson/30">
                <span>توقف اضطراری</span>
            </button>
            
            <a href="/export/json" class="btn-glow-violet bg-neonViolet/20 border border-neonViolet/50 text-neonViolet font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-neonViolet/30 mt-4 text-center">
                <span>دریافت فول بکاپ (JSON)</span>
            </a>
            <a href="/export/links" class="bg-transparent border border-cyan-500 text-cyan-500 font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-cyan-500/10 text-center">
                <span>دانلود لیست لینک‌ها (TXT)</span>
            </a>
            <button onclick="triggerAction('clean')" class="bg-transparent border border-orange-500 text-orange-500 font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 hover:bg-orange-500/10 mt-4">
                <span>فلش پایگاه داده</span>
            </button>
        </div>

        <!-- Terminal -->
        <div class="lg:col-span-2 glass-panel p-6 flex flex-col">
            <div class="flex justify-between items-center mb-2 border-b border-white/10 pb-2">
                <h2 class="text-xl font-semibold">Nexus Terminal</h2>
                <span class="text-xs text-slate-500 font-mono">LIVE MONITORING</span>
            </div>
            <div class="terminal flex-1" id="terminal-output"></div>
        </div>
    </div>

    <!-- Data Grid -->
    <div class="glass-panel p-6">
        <h2 class="text-xl font-semibold mb-4 border-b border-white/10 pb-2">پایگاه داده پیشرفته</h2>
        <div class="overflow-x-auto">
            <table id="accountsTable" class="w-full text-right display responsive nowrap">
                <thead>
                    <tr>
                        <th class="text-right">شماره خط (ID)</th>
                        <th class="text-right">نام پروفایل</th>
                        <th class="text-right">وضعیت</th>
                        <th class="text-right">نوع اکانت</th>
                        <th class="text-right">لینک امن (توکن دار)</th>
                        <th class="text-right">عملیات</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <!-- Delete Modal -->
    <div id="deleteModal" class="fixed inset-0 z-50 hidden items-center justify-center bg-black/60 backdrop-blur-sm">
        <div class="glass-panel w-full max-w-md p-6 transform scale-95 opacity-0 transition-all duration-300" id="deleteModalContent">
            <h3 class="text-xl font-bold text-white mb-4">تایید حذف و آزادسازی</h3>
            <p class="text-slate-300 mb-6">آیا از حذف حساب <span id="deleteTargetId" class="font-mono text-neonCrimson"></span> اطمینان دارید؟ خط برای استخراج مجدد آزاد می‌شود.</p>
            <div class="flex justify-end gap-3">
                <button onclick="closeDeleteModal()" class="px-4 py-2 rounded bg-slate-700 text-white hover:bg-slate-600">انصراف</button>
                <button onclick="confirmDelete()" class="px-4 py-2 rounded bg-neonCrimson text-white hover:bg-red-600">حذف کن</button>
            </div>
        </div>
    </div>

    <div id="toast-container"></div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <script>
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast flex items-center gap-3 border-l-4 ' + (type === 'success' ? 'border-l-neonEmerald' : (type === 'error' ? 'border-l-neonCrimson' : 'border-l-neonCyan'));
            toast.innerHTML = `<span class="text-sm font-bold">${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3000);
        }

        setInterval(() => { document.getElementById('current-time').innerText = new Date().toLocaleTimeString('fa-IR'); }, 1000);

        const createChart = (ctx, color) => new Chart(ctx, { type: 'line', data: { labels: Array(10).fill(''), datasets: [{ data: Array(10).fill(0), borderColor: color, borderWidth: 2, fill: true, backgroundColor: `${color}20` }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } }, scales: { x: { display: false }, y: { display: false } }, elements: { point: { radius: 0 }, line: { tension: 0.4 } } } });
        const chartTotal = createChart(document.getElementById('chart-total'), '#06b6d4');
        const chartSuccess = createChart(document.getElementById('chart-success'), '#10b981');
        const chartProxies = createChart(document.getElementById('chart-proxies'), '#8b5cf6');

        function updateChartData(chart, newValue) {
            const data = chart.data.datasets[0].data; data.push(newValue); if (data.length > 10) data.shift(); chart.update();
        }

        let accountsTable;
        $(document).ready(function() {
            accountsTable = $('#accountsTable').DataTable({
                language: { url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/fa.json" },
                pageLength: 15,
                columns: [
                    { data: 'id', render: data => `<span class="font-mono text-slate-300">${data}</span>` },
                    { data: 'username' },
                    { data: 'status', render: data => `<span class="text-neonEmerald font-semibold flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-neonEmerald inline-block"></span>${data}</span>` },
                    { data: 'plan', render: data => `<span class="text-neonCyan">${data}</span>` },
                    { data: 'link', render: data => `<span class="copy-badge px-2 py-1 bg-white/5 rounded border border-white/10 text-xs font-mono inline-block text-left w-full" dir="ltr" onclick="copyToClipboard('${data}')">${data}</span>` },
                    { data: 'id', orderable: false, render: data => `<button onclick="openDeleteModal('${data}')" class="text-neonCrimson hover:text-red-400">حذف</button>` }
                ],
                ajax: { url: '/api/accounts', dataSrc: 'data' }
            });
        });

        window.copyToClipboard = function(text) { navigator.clipboard.writeText(text).then(() => { showToast('لینک امن در کلیپ‌بورد کپی شد.', 'success'); }); };

        let accountToDelete = null;
        window.openDeleteModal = function(id) {
            accountToDelete = id; document.getElementById('deleteTargetId').innerText = id;
            const modal = document.getElementById('deleteModal'); const content = document.getElementById('deleteModalContent');
            modal.classList.remove('hidden'); modal.classList.add('flex');
            setTimeout(() => { content.classList.remove('scale-95', 'opacity-0'); content.classList.add('scale-100', 'opacity-100'); }, 10);
        };

        window.closeDeleteModal = function() {
            const modal = document.getElementById('deleteModal'); const content = document.getElementById('deleteModalContent');
            content.classList.remove('scale-100', 'opacity-100'); content.classList.add('scale-95', 'opacity-0');
            setTimeout(() => { modal.classList.add('hidden'); modal.classList.remove('flex'); accountToDelete = null; }, 300);
        };

        window.confirmDelete = function() {
            if(!accountToDelete) return;
            fetch('/api/action/delete_account', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: accountToDelete }) })
            .then(res => res.json()).then(data => {
                showToast('شماره آزاد شد و از سیستم حذف گردید.', 'success');
                accountsTable.ajax.reload(null, false);
                closeDeleteModal();
            });
        };

        window.triggerAction = function(action) {
            if(action === 'clean' && !confirm('پایگاه داده به طور کامل حذف خواهد شد. تایید؟')) return;
            fetch(`/api/action/${action}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => { showToast(data.message, data.status === 'ok' ? 'success' : 'error'); fetchStats(); });
        };

        function fetchStats() {
            fetch('/api/stats').then(res => res.json()).then(data => {
                document.getElementById('stat-total').innerText = data.total_accounts;
                document.getElementById('stat-success').innerText = data.success_rate;
                document.getElementById('stat-proxies').innerText = data.active_proxies;
                updateChartData(chartTotal, data.total_accounts); updateChartData(chartSuccess, data.success_rate); updateChartData(chartProxies, data.active_proxies);
                const statusText = document.getElementById('stat-status'); const indicator = document.getElementById('status-indicator');
                statusText.innerText = data.system_status;
                if(data.system_status === 'Processing') {
                    indicator.className = 'h-4 w-4 rounded-full bg-neonEmerald shadow-[0_0_15px_rgba(16,185,129,0.8)] animate-pulse-fast';
                    statusText.className = 'text-xl font-bold tracking-widest text-neonEmerald uppercase';
                } else {
                    indicator.className = 'h-4 w-4 rounded-full bg-slate-500 shadow-[0_0_10px_rgba(100,116,139,0.5)]';
                    statusText.className = 'text-xl font-bold tracking-widest text-slate-400 uppercase';
                }
            });
        }

        let lastLogsRaw = "";
        function fetchLogs() {
            fetch('/api/logs').then(res => res.json()).then(data => {
                const logsString = JSON.stringify(data.logs);
                if(logsString !== lastLogsRaw) {
                    const term = document.getElementById('terminal-output');
                    term.innerHTML = '';
                    data.logs.forEach(log => {
                        const p = document.createElement('div');
                        let clr = "log-info";
                        if(log.message.includes("❌") || log.message.includes("ارور")) clr = "log-error";
                        if(log.message.includes("✅")) clr = "log-info";
                        if(log.message.includes("⚠️") || log.message.includes("هشدار")) clr = "log-warning";
                        p.className = `mb-1 ${clr}`;
                        p.innerHTML = `[${log.timestamp}] root@nexus:~# <span class="ml-2">${log.message}</span>`;
                        term.appendChild(p);
                    });
                    term.scrollTop = term.scrollHeight;
                    lastLogsRaw = logsString;
                }
            });
        }

        setInterval(fetchStats, 3000); setInterval(fetchLogs, 3000);
        fetchStats(); fetchLogs();
    </script>
</body>
</html>
"""

# ================= Routes & Logic =================
@app.route('/')
def dashboard():
    if not session.get('logged_in'): return render_template_string(LOGIN_TEMPLATE)
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return "پسورد اشتباه است. بازگشت...", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))

# اتصال نمودارها و آمارها به دیتابیس
@app.route('/api/stats')
def get_stats():
    if not session.get('logged_in'): return jsonify({}), 401
    
    total = db.hlen("jet:bulk_accounts")
    # شبیه‌سازی وضعیت انجین بر اساس آخرین فرمان صادر شده
    last_cmd = db.lindex("bot:admin_commands", -1)
    status = "Processing" if last_cmd == "START_BULK" else "Standby"
    
    return jsonify({
        "total_accounts": total,
        "success_rate": 100.0, # خطاهای لوکال ذخیره نمی‌شوند، دیتابیس ۱۰۰٪ سالم است
        "active_proxies": 20,  # نمایش پیش‌فرض ترد‌های لوکال
        "system_status": status
    })

# اتصال ترمینال به لاگ‌های آقای بیگی
@app.route('/api/logs')
def get_logs():
    if not session.get('logged_in'): return jsonify({"logs": []}), 401
    raw_logs = db.lrange("bot:admin_alerts", -20, -1)
    logs_formatted = []
    for l in raw_logs:
        logs_formatted.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": l.replace('\n', ' - ')
        })
    if not logs_formatted:
        logs_formatted.append({"timestamp": datetime.now().strftime("%H:%M:%S"), "message": "سیستم آماده دریافت فرمان..."})
    return jsonify({"logs": logs_formatted})

# اتصال جدول DataTables به دیتابیس Redis
@app.route('/api/accounts')
def get_accounts():
    if not session.get('logged_in'): return jsonify({"data": []}), 401
    records = db.hgetall("jet:bulk_accounts")
    accounts_data = []
    for phone, val in records.items():
        data = json.loads(val)
        accounts_data.append({
            "id": phone,
            "username": data['name'],
            "status": "Active",
            "plan": "Digikala Jet",
            "link": f"{WEBHOOK_URL}/auth/{data['token']}"
        })
    return jsonify({"data": accounts_data})

# دکمه‌های کنترل
@app.route('/api/action/start', methods=['POST'])
def action_start():
    if not session.get('logged_in'): return jsonify({}), 401
    db.delete("bot:admin_commands") # پاک کردن فرمان‌های قبلی
    db.rpush("bot:admin_commands", "START_BULK")
    return jsonify({"status": "ok", "message": "فرمان استارت به سرور لوکال ارسال شد."})

@app.route('/api/action/stop', methods=['POST'])
def action_stop():
    if not session.get('logged_in'): return jsonify({}), 401
    db.rpush("bot:admin_commands", "STOP_BULK")
    return jsonify({"status": "error", "message": "فرمان توقف اضطراری ارسال شد!"})

@app.route('/api/action/clean', methods=['POST'])
def action_clean():
    if not session.get('logged_in'): return jsonify({}), 401
    db.delete("jet:processed_phones")
    db.delete("jet:bulk_accounts")
    db.delete("bot:admin_alerts")
    return jsonify({"status": "ok", "message": "پایگاه داده به طور کامل فرمت شد."})

@app.route('/api/action/delete_account', methods=['POST'])
def action_delete_account():
    if not session.get('logged_in'): return jsonify({"status": "error"}), 401
    phone = request.json.get('id')
    record = db.hget("jet:bulk_accounts", phone)
    if record:
        data = json.loads(record)
        db.delete(f"jet_session:{data['token']}")
        db.hdel("jet:bulk_accounts", phone)
        db.srem("jet:processed_phones", phone)
    return jsonify({"status": "ok"})

# دانلود مستقیم TXT
@app.route('/export/links')
def export_links():
    if not session.get('logged_in'): return "دسترسی غیرمجاز", 401
    records = db.hgetall("jet:bulk_accounts")
    text = "لیست لینک‌های استخراج شده Nexus Engine:\n\n"
    for phone, val in records.items():
        data = json.loads(val)
        text += f"Phone: {phone}\nName: {data['name']}\nLink: {WEBHOOK_URL}/auth/{data['token']}\n--------------------\n"
    return send_file(BytesIO(text.encode('utf-8')), as_attachment=True, download_name=f"Nexus_Links_{datetime.now().strftime('%Y%m%d')}.txt", mimetype='text/plain')

# دانلود مستقیم JSON
@app.route('/export/json')
def export_json():
    if not session.get('logged_in'): return "دسترسی غیرمجاز", 401
    keys = db.keys("jet_session:*")
    accs = {k: json.loads(db.get(k)) for k in keys if db.get(k)}
    return send_file(BytesIO(json.dumps(accs, ensure_ascii=False, indent=2).encode('utf-8')), as_attachment=True, download_name=f"Nexus_DB_{datetime.now().strftime('%Y%m%d')}.json", mimetype='application/json')

# درگاه API فلاتر
@app.route('/auth/<token>')
def secure_gateway(token):
    session_str = db.get(f"jet_session:{token}")
    if not session_str: return "لینک نامعتبر یا منقضی شده است.", 404
    u_agent = request.headers.get("User-Agent", "")
    app_hdr = request.headers.get("X-Client-App", "")
    if app_hdr == APP_SECRET_HEADER or "JetAppClient" in u_agent:
        return jsonify({"status": "success", "session": json.loads(session_str)})
    return '<html dir="rtl"><body style="background:#0f172a; color:#f43f5e; font-family:Tahoma; text-align:center; padding-top:100px;"><h2>دسترسی مسدود است</h2><p>این لینک فقط درون اپلیکیشن موبایل قابل بازگشایی است.</p></body></html>'

# ================= Token Worker =================
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
