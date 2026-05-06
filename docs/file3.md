# Hướng dẫn Kiểm thử (Testing) Hệ thống Ansible

## Yêu cầu

* Đã clone project và hoàn tất setup môi trường (`docs/Setup.md`)
* Control Node đã cài:

  * Ansible
  * sshpass
  * Python3
* node1 (`192.168.80.139`) và node2 (`192.168.80.140`) đang hoạt động
* SSH giữa các node hoạt động bình thường

---

# Bước 1 — Thiết lập Vault Password trước khi Demo

## Mục đích

Cấu hình Ansible tự đọc mật khẩu Vault để khi demo không cần nhập `--ask-vault-pass`.

---

## 1.1 Tạo file chứa mật khẩu Vault

```bash id="q5w9ln"
echo "vault_password_123" > ~/.vault_pass
```

> Thay `vault_password_123` bằng mật khẩu Vault thực tế của project.

---

## 1.2 Phân quyền bảo mật

```bash id="f2r8tx"
chmod 600 ~/.vault_pass
```

---

## 1.3 Cấu hình ansible.cfg

Mở file:

```bash id="g8m1qy"
nano ansible.cfg
```

Cập nhật:

```ini id="v4c7kp"
[defaults]
inventory = inventories/dynamic_inventory.py
host_key_checking = False
vault_password_file = ~/.vault_pass
roles_path = ./roles
```

---

## 1.4 Kiểm tra Vault

```bash id="t9n3hw"
ansible-vault view vault/secrets.yml
```

## Kết quả đúng

Không hỏi password và hiển thị nội dung YAML:

```yaml id="d7k4vm"
mysql_root_password: root_password
mysql_user: appuser
mysql_password: app_password
```

---

# Bước 2 — Cài đặt Dependencies (Ansible Galaxy)

## Mục đích

Đảm bảo các collections cần thiết đã được cài đặt.

```bash id="a3x8pf"
ansible-galaxy collection install -r requirements.yml
```

## Kết quả mong đợi

```text id="n7q1zl"
Starting galaxy collection install process
...
Nothing to do. All requested collections are already installed.
```

Hoặc:

```text id="j2p5vr"
community.docker was installed successfully
community.mysql was installed successfully
```

---

# Bước 3 — Test Dynamic Inventory

## Mục đích

Kiểm tra script Dynamic Inventory hoạt động đúng.

---

## 3.1 Test script sinh JSON

```bash id="u4m9kc"
python3 inventories/dynamic_inventory.py --list
```

## Kết quả mong đợi

Trả về JSON chứa:

* `web`
* `db`
* `_meta`

Ví dụ:

```json id="y6r2tw"
{
  "web": {
    "hosts": ["node1"]
  },
  "db": {
    "hosts": ["node2"]
  }
}
```

---

## 3.2 Test Ansible đọc Inventory

```bash id="s1q8xh"
ansible -i inventories/dynamic_inventory.py all --list-hosts
```

## Kết quả mong đợi

```text id="l3d7vn"
hosts (2):
  node1
  node2
```

---

# Bước 4 — Deploy hệ thống lần đầu

## Mục đích

Triển khai toàn bộ:

* Docker
* MySQL
* Flask
* Nginx
* Firewall

---

## Chạy Playbook

```bash id="c5t9qm"
ansible-playbook playbooks/site.yml
```

---

## Kết quả mong đợi

* Terminal hiển thị task màu xanh (`ok`) hoặc vàng (`changed`)
* Không xuất hiện `FAILED`
* PLAY RECAP kết thúc với `failed=0`

Ví dụ:

```text id="k8x2bf"
PLAY RECAP
node1 : ok=33 changed=6 failed=0
node2 : ok=25 changed=3 failed=0
```

---

## Kiểm tra Web

Mở trình duyệt:

```text id="m7p4zd"
http://192.168.80.139
```

## Web hiển thị:

* Danh sách server
* Deployment logs
* Database connection status
* Deployment time

---

# Bước 5 — Test Tags & Dry-run (Check Mode)

## Mục đích

Chạy thử playbook mà không thay đổi hệ thống thật.

---

## Chạy riêng Web role bằng Check Mode

```bash id="w9q6lt"
ansible-playbook playbooks/site.yml --tags webapp --check
```

---

## Kết quả mong đợi

* Chỉ các task có tag `webapp` được chạy
* Docker/MySQL bị bỏ qua
* Chủ yếu hiển thị:

  * `ok`
  * `skipping`

Hệ thống thực tế không bị thay đổi.

---

# Bước 6 — Test tính năng Backup

## Mục đích

Tạo backup:

* source Flask
* dữ liệu MySQL

---

## Chạy Backup Playbook

```bash id="h4r8py"
ansible-playbook playbooks/backup.yml
```

---

## 6.1 Kiểm tra Backup Web

```bash id="q1m7tv"
ssh vagrant@192.168.80.139 \
"sudo ls -la /opt/backups/webapp/"
```

## Kết quả mong đợi

```text id="u8d3cx"
latest.tar.gz
webapp_2025_xxxx.tar.gz
```

* `latest.tar.gz` là symlink
* `.tar.gz` chứa source Flask app

---

## 6.2 Kiểm tra Backup Database

```bash id="x5v1nh"
ssh vagrant@192.168.80.140 \
"sudo ls -la /opt/backups/mysql/"
```

## Kết quả mong đợi

```text id="p7k2mf"
latest.sql.gz
mysql_2025_xxxx.sql.gz
```

* `.sql.gz` chứa MySQL dump

---

# Bước 7 — Test Health Check & Rollback

## Mục đích

Mô phỏng sự cố và kiểm tra khả năng tự phục hồi hệ thống.

---

# 7.1 Đánh sập Flask Container

```bash id="n4y8zr"
ssh vagrant@192.168.80.139 \
"sudo docker stop flask_app"
```

---

## Kết quả mong đợi

* Web không truy cập được
* Trình duyệt có thể:

  * loading vô hạn
  * báo `502 Bad Gateway`

---

# 7.2 Chạy Health Check

```bash id="f6q3kw"
ansible-playbook playbooks/healthcheck.yml
```

---

## Kết quả mong đợi

Terminal báo FAILED màu đỏ tại task:

```text id="r9t1vc"
Assert Flask container dang chay
```

Summary:

```text id="z2m8hb"
Flask container : FAIL
```

Điều này xác nhận hệ thống đã phát hiện sự cố thành công.

---

# 7.3 Chạy Rollback Playbook

```bash id="e3p7xn"
ansible-playbook playbooks/rollback.yml
```

---

## Kết quả mong đợi

Playbook tự động:

* giải nén backup
* restore source code
* khởi động lại Flask container
* verify service

---

# 7.4 Kiểm tra hệ thống sau Rollback

```bash id="k1x6mw"
ansible-playbook playbooks/healthcheck.yml
```

---

## Kết quả mong đợi

Toàn bộ service hiển thị:

```text id="c8v5py"
OK
```

Ví dụ:

```text id="v3m7qa"
Flask container : OK
MySQL connection : OK
HTTP endpoint : OK
```

F5 trình duyệt:

* Web hoạt động bình thường trở lại
* Deployment logs vẫn còn
* Database không mất dữ liệu

---

# Một số lệnh debug nhanh

## Kiểm tra Docker Containers

```bash id="g5q2xt"
docker ps
```

---

## Kiểm tra Flask Logs

```bash id="s7k4mn"
docker logs flask_app
```

---

## Kiểm tra MySQL Logs

```bash id="t1y8vf"
docker logs mysql
```

---

## Kiểm tra Firewall

```bash id="u6r3pk"
sudo ufw status
```

---

# Lưu ý

* Không commit `.vault_pass` lên GitHub
* Backup nên chạy trước mỗi lần deploy lớn
* Khi đổi IP node cần cập nhật inventory
* Nếu Docker pull chậm nên cấu hình registry mirror
