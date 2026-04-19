from flask import Flask
import pymysql
import os
from datetime import datetime

app = Flask(__name__)

# Bien moi truong do Ansible truyen vao luc deploy
DB_HOST     = os.environ.get("DB_HOST",     "localhost")
DB_PORT     = int(os.environ.get("DB_PORT", 3306))
DB_NAME     = os.environ.get("DB_NAME",     "ansible_iac_db")
DB_USER     = os.environ.get("DB_USER",     "root")
DB_PASS     = os.environ.get("DB_PASS",     "")
SERVER_NAME = os.environ.get("SERVER_NAME", "node1")
SERVER_IP   = os.environ.get("SERVER_IP",   "unknown")

def query_db(sql):
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            database=DB_NAME, charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
        return rows, None
    except Exception as e:
        return [], str(e)

@app.route("/")
def index():
    servers,  err1 = query_db("SELECT * FROM servers ORDER BY id")
    logs,     err2 = query_db("SELECT * FROM deploy_logs ORDER BY id")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang='vi'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Ansible IAC Project</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',sans-serif;background:#0f0f1a;color:#e2e2f0;padding:32px 16px}}
    .container{{max-width:900px;margin:auto}}

    .header{{background:#16213e;border:1px solid #2a2a5a;border-radius:16px;
             padding:32px;text-align:center;margin-bottom:24px}}
    .header h1{{font-size:2rem;color:#e94560;letter-spacing:1px}}
    .header p{{color:#8888aa;margin-top:8px}}
    .badges{{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:16px}}
    .badge{{background:#0f3460;border:1px solid #1a5a9a;border-radius:20px;
            padding:5px 16px;font-size:.82rem;color:#7ec8e3}}
    .badge span{{color:#fff;font-weight:600}}

    .card{{background:#16213e;border:1px solid #2a2a5a;border-radius:12px;
           padding:24px;margin-bottom:20px}}
    .card h2{{font-size:.9rem;color:#7ec8e3;text-transform:uppercase;
              letter-spacing:1.5px;margin-bottom:16px;padding-bottom:10px;
              border-bottom:1px solid #2a2a5a}}

    table{{width:100%;border-collapse:collapse}}
    th{{background:#0f3460;color:#7ec8e3;padding:10px 14px;
        text-align:left;font-size:.82rem;text-transform:uppercase;letter-spacing:1px}}
    td{{padding:10px 14px;border-bottom:1px solid #1e1e3a;
        font-size:.9rem;color:#c8c8e0}}
    tr:last-child td{{border-bottom:none}}
    tr:hover td{{background:#1a2a4a}}

    .tag{{display:inline-block;padding:3px 10px;border-radius:12px;
          font-size:.78rem;font-weight:600}}
    .tag-green{{background:#0d3320;color:#4caf50;border:1px solid #2d6640}}
    .tag-blue{{background:#0d2033;color:#64b5f6;border:1px solid #1a4466}}
    .tag-orange{{background:#2d1a00;color:#ffb74d;border:1px solid #664400}}

    .db-info{{background:#0a1628;border:1px solid #1a3050;border-radius:8px;
              padding:12px 16px;margin-bottom:16px;font-size:.82rem;color:#556688}}

    .footer{{text-align:center;color:#3a3a5a;font-size:.8rem;margin-top:8px}}
  </style>
</head>
<body>
<div class='container'>

  <div class='header'>
    <h1>Ansible IAC Project</h1>
    <p>Infrastructure as Code — Tu dong hoa ha tang bang Ansible + Flask + MySQL</p>
    <div class='badges'>
      <div class='badge'>Server: <span>{SERVER_NAME}</span></div>
      <div class='badge'>IP: <span>{SERVER_IP}</span></div>
      <div class='badge'>DB: <span>{DB_NAME}@{DB_HOST}</span></div>
      <div class='badge'>Deploy: <span>{now}</span></div>
    </div>
  </div>

  <div class='card'>
    <h2>Danh sach Server (doc tu MySQL — {DB_NAME})</h2>
    <div class='db-info'>
      Ket noi: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}
      {"&nbsp;&nbsp;|&nbsp;&nbsp;<span style='color:#e94560'>Loi: " + err1 + "</span>" if err1 else "&nbsp;&nbsp;|&nbsp;&nbsp;<span style='color:#4caf50'>Connected OK</span>"}
    </div>
    <table>
      <thead><tr><th>#</th><th>Hostname</th><th>IP</th><th>Role</th><th>Status</th><th>Deployed at</th></tr></thead>
      <tbody>"""

    if servers:
        for s in servers:
            role_tag  = "tag-blue"   if s["role"]   == "web"     else "tag-orange"
            stat_tag  = "tag-green"  if s["status"]  == "running" else ""
            html += f"""
        <tr>
          <td>{s['id']}</td>
          <td><b>{s['hostname']}</b></td>
          <td>{s['ip']}</td>
          <td><span class='tag {role_tag}'>{s['role']}</span></td>
          <td><span class='tag {stat_tag}'>{s['status']}</span></td>
          <td>{s['deployed_at']}</td>
        </tr>"""
    else:
        html += "<tr><td colspan='6' style='color:#556688;text-align:center'>Chua co data</td></tr>"

    html += """
      </tbody>
    </table>
  </div>

  <div class='card'>
    <h2>Deploy Logs (doc tu MySQL)</h2>
    <table>
      <thead><tr><th>#</th><th>Server</th><th>Task</th><th>Result</th><th>Time</th></tr></thead>
      <tbody>"""

    if logs:
        for l in logs:
            tag = "tag-green" if l["result"] == "success" else "tag-orange"
            html += f"""
        <tr>
          <td>{l['id']}</td>
          <td>{l['server']}</td>
          <td>{l['task']}</td>
          <td><span class='tag {tag}'>{l['result']}</span></td>
          <td>{l['created_at']}</td>
        </tr>"""
    else:
        html += "<tr><td colspan='5' style='color:#556688;text-align:center'>Chua co data</td></tr>"

    html += f"""
      </tbody>
    </table>
  </div>

  <div class='footer'>
    Ansible IAC Project &nbsp;|&nbsp; Flask/Python &nbsp;|&nbsp; {now}
  </div>

</div>
</body>
</html>"""
    return html

@app.route("/health")
def health():
    _, err = query_db("SELECT 1")
    if err:
        return {{"status": "error", "db": err}}, 500
    return {{"status": "ok", "server": SERVER_NAME, "db": DB_NAME}}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
