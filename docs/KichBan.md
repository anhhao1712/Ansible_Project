# 🧪 Testing Guide — Ansible IAC Project

---

# Bước 1 — Cài Dependencies

```bash
ansible-galaxy collection install -r requirements.yml
```

---

## Bước 2: Tạo và mã hóa file secrets

### Tạo file secrets:

```bash
cat > vault/secrets.yml << EOF
vault_mysql_root_password: "Root@1234"
vault_mysql_password: "Wp@1234"
EOF
```

---

### Mã hóa file:

```bash
ansible-vault encrypt vault/secrets.yml
```

Nhập password khi được yêu cầu:

```text
@Hao1712
```

---

### Cấu hình tự động giải mã khi được yêu cầu nhập password các lệnh cần quyền quản trị:

```bash
echo "@Hao1712" > ~/.vault_pass
chmod 600 ~/.vault_pass
```

---

# Kết quả

### Hiển thị file mã hóa:

```bash
cat vault/secrets.yml
```

```text
$ANSIBLE_VAULT;1.1;AES256
(dạng mã hóa)
```

---

### Chạy Ansible không cần nhập password:

```bash
ansible-vault view vault/secrets.yml
```

```yaml
vault_mysql_root_password: "Root@1234"
vault_mysql_password: "Wp@1234"
```

# Bước 3 — Deploy hệ thống

```bash
ansible-playbook playbooks/site.yml
```

---

# Bước 4 — Test Tags & Dry-run

```bash
ssh vagrant@192.168.80.139 "sudo docker stop flask_app"
```

```bash
ansible-playbook playbooks/site.yml --tags webapp
```

---

# Bước 5 — Test Backup

```bash
ansible-playbook playbooks/backup.yml
```

## Kiểm tra backup Web

```bash
ssh vagrant@192.168.80.139 "sudo ls -la /opt/backups/webapp/"
```

## Kiểm tra backup Database

```bash
ssh vagrant@192.168.80.140 "sudo ls -la /opt/backups/mysql/"
```

---

# Bước 6 — Test Health Check & Rollback

## 6.1 — Tắt Flask Container

```bash
ssh vagrant@192.168.80.139 'cat << "EOF" > /tmp/hacked_app.py
from flask import Flask
app = Flask(__name__)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def hack(path):
    return "<h1 style=\"color:red;font-size:100px;text-align:center;margin-top:20%;\">HỆ THỐNG ĐÃ BỊ HACK</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF
sudo docker cp /tmp/hacked_app.py flask_app:/app/app.py
sudo docker restart flask_app'
```

---

## 6.2 — Health Check

```bash
ansible-playbook playbooks/healthcheck.yml
```

---

## 6.3 — Rollback

```bash
ansible-playbook playbooks/rollback.yml
```

---

## 6.4 — Kiểm tra lại

```bash
ansible-playbook playbooks/healthcheck.yml
```
