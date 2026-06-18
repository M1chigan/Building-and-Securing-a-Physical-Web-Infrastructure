import signal

from flask import Flask, redirect, request, url_for, session, render_template_string
import os
import subprocess
import requests
import re

app = Flask(__name__)
app.secret_key = 'starmooc_final_secure_key_2026'

# Cache pour éviter de saturer l'API de géolocalisation
geo_cache = {}

def get_country(ip):
    if not ip or ip.startswith(("192.", "10.", "172.16.", "127.", "fe80")): 
        return "local"
    if ip in geo_cache: 
        return geo_cache[ip]
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=1)
        if r.status_code == 200 and r.json().get('status') == 'success':
            code = r.json().get('countryCode').lower()
            geo_cache[ip] = code
            return code
    except:
        pass
    return "un"

def get_command_output(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode()
    except:
        return ""

# --- PAGE 1 : MONITORING CENTER ---
@app.route('/')
def dashboard():
    skip_suricata = session.get('suricata_skip', 0)
    skip_ssh = session.get('ssh_skip', 0)
    
    # 1. Firewall Status
    ufw_raw = get_command_output("sudo ufw status | grep -i 'Status'")
    ufw_status = ufw_raw.replace("Status: ", "").strip() if ufw_raw else "Unknown"
    
    # 2. Fail2Ban Status avec drapeaux
    f2b_raw = get_command_output("sudo fail2ban-client status sshd | grep 'Banned IP list'")
    f2b_ips = []
    ips_found = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', f2b_raw)
    for ip in ips_found:
        f2b_ips.append({"ip": ip, "country": get_country(ip)})

    # 3. Suricata Alerts (Lecture sécurisée)
    suricata_items = []
    log_suricata = "/var/log/suricata/fast.log"
    if os.path.exists(log_suricata):
        try:
            with open(log_suricata, "r") as f:
                lines = f.readlines()
                if skip_suricata > len(lines): skip_suricata = 0 # Reset si log vidé
                
                display_lines = lines[skip_suricata:]
                for line in display_lines[-12:]: # 12 dernières alertes
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                    ip = ip_match.group(1) if ip_match else ""
                    country = get_country(ip)
                    suricata_items.append({"text": line.strip(), "country": country})
        except Exception as e:
            suricata_items.append({"text": f"Error reading Suricata logs: {str(e)}", "country": "un"})

    # 4. SSH Logs
    ssh_log = ""
    try:
        raw_ssh = get_command_output("grep 'Failed password' /var/log/auth.log").splitlines()
        if skip_ssh > len(raw_ssh): skip_ssh = 0
        ssh_log = "\n".join(raw_ssh[skip_ssh:][-6:])
    except:
        ssh_log = "No failed SSH attempts found."

    return render_template_string(f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="5">
        <title>Security Center</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; margin: 0; }}
            .container {{ width: 95%; max-width: 1400px; margin: auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 20px; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            h2 {{ color: #58a6ff; margin-top: 0; display: flex; justify-content: space-between; align-items: center; font-size: 1.2em; }}
            .log-entry {{ border-bottom: 1px solid #21262d; padding: 6px 0; display: flex; align-items: center; font-family: 'Consolas', monospace; font-size: 0.85em; }}
            .flag {{ width: 22px; margin-right: 12px; border-radius: 2px; border: 1px solid #333; }}
            .flag-small {{ width: 18px; margin-right: 5px; vertical-align: middle; }}
            pre {{ background: #000; color: #39d353; padding: 12px; border-radius: 5px; font-size: 0.9em; border: 1px solid #222; white-space: pre-wrap; }}
            .btn {{ background: #238636; color: white; border: none; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 0.75em; cursor: pointer; }}
            .btn-clear {{ background: #da3633; }}
            .nav-link {{ color: #58a6ff; text-decoration: none; font-weight: bold; border: 1px solid #58a6ff; padding: 8px 15px; border-radius: 5px; transition: 0.3s; }}
            .nav-link:hover {{ background: #58a6ff; color: #0d1117; }}
            .status-tag {{ color: #7ee787; font-weight: bold; border: 1px solid #238636; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; }}
            .ip-box {{ display: inline-block; background: #21262d; padding: 4px 10px; border-radius: 4px; margin: 4px; border: 1px solid #30363d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Perimeter Security Monitor</h1>
                <a href="/analytics" class="nav-link">📊 VIEW ANALYTICS</a>
            </div>

            <div class="card" style="border-left: 5px solid #238636;">
                <h2>🧱 Firewall Status <span class="status-tag">{ufw_status}</span></h2>
            </div>

            <div class="card" style="border-left: 5px solid #d29922;">
                <h2>🚫 Fail2Ban : Currently Banned IPs</h2>
                <div>
                    {" ".join([f'<span class="ip-box"><img src="https://flagcdn.com/w20/{ip["country"]}.png" class="flag-small"> {ip["ip"]}</span>' for ip in f2b_ips]) if f2b_ips else "No active bans."}
                </div>
            </div>

            <div class="card" style="border-left: 5px solid #f85149;">
                <h2>🚨 Intrusion Detection (Suricata) <a href="/clear/suri" class="btn btn-clear">Clear Suricata</a></h2>
                <div id="suricata-logs">
                    {"".join([f'<div class="log-entry"><img src="https://flagcdn.com/w40/{item["country"]}.png" class="flag"><span>{item["text"]}</span></div>' for item in suricata_items]) if suricata_items else "No recent alerts detected."}
                </div>
            </div>

            <div class="card">
                <h2>🔑 SSH Authentication Failures <a href="/clear/ssh" class="btn btn-clear">Clear SSH Logs</a></h2>
                <pre>{ssh_log if ssh_log else "No failed login attempts."}</pre>
            </div>
        </div>
    </body>
    </html>
    """)

# --- PAGE 2 : ANALYTICS ---
@app.route('/analytics')
def analytics():
    p, s, o = 0, 0, 0
    skip_suri = session.get('suricata_skip', 0)
    skip_ssh = session.get('ssh_skip', 0)

    if os.path.exists("/var/log/suricata/fast.log"):
        with open("/var/log/suricata/fast.log", "r") as f:
            lines = f.readlines()[skip_suri:]
            for l in lines:
                if "PING" in l: p += 1
                else: o += 1
    try:
        raw_ssh = get_command_output("grep 'Failed password' /var/log/auth.log").splitlines()
        s = len(raw_ssh[skip_ssh:])
    except:
        pass

    return render_template_string(f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="5">
        <title>Threat Analytics</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #0b0e14; color: white; margin: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; position: relative; }}
            .container {{ background: #1c2128; padding: 40px; border-radius: 20px; border: 1px solid #2d333b; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; width: 600px; }}
            h1 {{ color: #58a6ff; margin-bottom: 20px; }}
            .close-btn {{ position: absolute; top: 30px; right: 30px; font-size: 40px; color: #f85149; text-decoration: none; font-weight: bold; transition: 0.2s; }}
            .close-btn:hover {{ transform: scale(1.2); color: white; }}
        </style>
    </head>
    <body>
        <a href="/" class="close-btn" title="Back to Dashboard">✖</a>
        
        <div class="container">
            <h1>📊 Threat Distribution</h1>
            <canvas id="threatChart"></canvas>
            <p style="margin-top: 20px; color: #8b949e;">Visual analysis of real-time security events</p>
        </div>

        <script>
            const ctx = document.getElementById('threatChart').getContext('2d');
            new Chart(ctx, {{
                type: 'polarArea',
                data: {{
                    labels: ['Ping (ICMP)', 'SSH Failures', 'Other (Suricata)'],
                    datasets: [{{
                        data: [{p}, {s}, {o}],
                        backgroundColor: ['rgba(88,166,255,0.7)', 'rgba(248,81,73,0.7)', 'rgba(240,136,62,0.7)'],
                        borderColor: ['#58a6ff', '#f85149', '#f0883e'],
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    scales: {{ r: {{ grid: {{ color: '#30363d' }}, ticks: {{ display: false }} }} }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff', font: {{ size: 14 }} }} }} }}
                }}
            }});
        </script>
    </body>
    </html>
    """)

@app.route('/clear/suri')
def clear_suri():
    if os.path.exists("/var/log/suricata/fast.log"):
        with open("/var/log/suricata/fast.log", "r") as f:
            session['suricata_skip'] = len(f.readlines())
    return redirect(url_for('dashboard'))

@app.route('/clear/ssh')
def clear_ssh():
    try:
        raw_ssh = get_command_output("grep 'Failed password' /var/log/auth.log").splitlines()
        session['ssh_skip'] = len(raw_ssh)
    except:
        pass
    return redirect(url_for('dashboard'))

@app.route('/crash')
def crash():
    os.kill(os.getpid(), signal.SIGKILL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        return f"Login attempted for {username}. (Sent in plain text!)"
    return render_template_string("""
        <body style="background:#0d1117; color:white; display:flex; justify-content:center; align-items:center; height:100vh; flex-direction:column;">
            <h2>Insecure Login Portal</h2>
            <form method="POST"><input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Login (Unsecured)</button></form>
        </body>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)