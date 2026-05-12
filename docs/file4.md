# Hướng dẫn chạy Ansible Project v2 — Từ đầu đến demo

## Tổng quan kiến trúc

```
[Máy tính / Control Node]
        │  SSH
        ├─────────────────────────────────────────────┐
        │                                             │
        ▼                                             ▼
  node1 (192.168.80.139)                    node2 (192.168.80.140)
  ┌─────────────────────┐                   ┌──────────────────┐
  │ Nginx LB  :80       │                   │ MySQL 8.0  :3306 │
  │ Flask App :5000     │◄──── DB ──────────│                  │
  └─────────────────────┘                   └──────────────────┘
        │ LB round-robin
        ▼
  node3 (192.168.80.141)
  ┌─────────────────────┐
  │ Flask App :5000     │
  └─────────────────────┘
```

---

## PHẦN 1: Chuẩn bị môi trường

### 1.1 Cài Ansible trên máy tính (Control Node)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ansible python3-pip -y

# macOS
brew install ansible

# Kiểm tra
ansible --version   # cần >= 2.14
python3 --version   # cần >= 3.9
```

### 1.2 Cài Python dependencies

```bash
pip3 install paramiko pymysql
```

### 1.3 Giải nén project

```bash
# Giải nén RAR
unrar x Ansible_Project_v2.rar
cd Ansible_Project_v2
```

### 1.4 Cài Ansible Galaxy collections

```bash
ansible-galaxy collection install -r requirements.yml
```

Lệnh này cài:
- `community.docker` — quản lý Docker containers
- `community.general` — các module tổng hợp
- `community.mysql` — quản lý MySQL
- `community.crypto` — SSL/crypto

---

## PHẦN 2: Tạo các VMs

### 2.1 Khởi động node1 và node2 bằng Vagrant

```bash
vagrant up node1 node2
```

Vagrant tự động:
- Tạo 2 VM Ubuntu 20.04
- Gán IP tĩnh: node1=`192.168.80.139`, node2=`192.168.80.140`
- Cài Python3, SSH

### 2.2 Tạo node3 (clone từ node1)

**Trong VMware:**
1. Right-click VM `ansible-lab-node1` → **Clone**
2. Chọn **Full Clone**
3. Đặt tên: `ansible-lab-node3`
4. Sau khi clone xong, **bật VM node3** lên

**Đổi IP node3 thành `192.168.80.141`:**

```bash
# SSH vào node3 (lúc đầu nó có IP của node1)
# Tìm IP hiện tại qua VMware console hoặc DHCP

# Sau khi SSH vào:
sudo nano /etc/netplan/01-netcfg.yaml
```

Sửa nội dung thành:
```yaml
network:
  version: 2
  ethernets:
    eth1:
      addresses:
        - 192.168.80.141/24
```

```bash
sudo netplan apply
hostname   # Nên đổi thành node3
sudo hostnamectl set-hostname node3
```

> **Lưu ý:** Nếu dùng VirtualBox thì dùng `ip addr` để kiểm tra interface name thay vì eth1.

### 2.3 Kiểm tra kết nối 3 nodes

```bash
ansible all -m ping
```

Kết quả mong đợi:
```
node1 | SUCCESS => {"ping": "pong"}
node2 | SUCCESS => {"ping": "pong"}
node3 | SUCCESS => {"ping": "pong"}
```

Nếu node3 lỗi: kiểm tra lại IP và SSH `ssh vagrant@192.168.80.141`.

---

## PHẦN 3: Deploy toàn bộ hệ thống

### 3.1 (Tuỳ chọn) Mở Ansible Vault nếu cần chỉnh secrets

```bash
# Xem nội dung vault
ansible-vault view vault/secrets.yml

# Sửa secrets
ansible-vault edit vault/secrets.yml
# Password vault mặc định: "vagrant" (hoặc xem docs/Setup.md)
```

### 3.2 Deploy

```bash
ansible-playbook playbooks/site.yml
```

**Thứ tự deploy:**

| Play | Hosts | Nội dung |
|------|-------|---------|
| Play 1 | all | Test biến global |
| Play 2 | node2 | Docker + MySQL + Security |
| Play 3 | node1, node3 | Docker + Flask App + Security |
| Play 4 | node1 | Nginx Load Balancer |

Mất khoảng **5–10 phút** tùy tốc độ mạng (pull Docker images).

### 3.3 Kiểm tra sau deploy

```bash
ansible-playbook playbooks/healthcheck.yml
```

---

## PHẦN 4: Kiểm tra hệ thống hoạt động

### 4.1 Mở browser

Truy cập: **http://192.168.80.139**

Thấy trang Flask app với:
- Badge **v1.0** màu xanh dương
- Bảng server list từ MySQL
- Badge "Server: node1" hoặc "node3" (tuỳ request)

### 4.2 Kiểm tra Load Balancer round-robin

```bash
# Chạy 10 request liên tiếp, xem server thay đổi
for i in $(seq 1 10); do
  curl -s http://192.168.80.139/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['server'])"
done
```

Kết quả mong đợi:
```
node1
node3
node1
node3
...
```

### 4.3 Xem config Nginx LB hiện tại

```bash
ssh vagrant@192.168.80.139 'cat /tmp/nginx_conf/default.conf'
```

---

## PHẦN 5: Demo Rolling Update

### 5.1 Mở 2 terminal song song

**Terminal A** — Theo dõi traffic liên tục:
```bash
watch -n 0.5 'curl -s http://192.168.80.139/health'
```

**Terminal B** — Chạy rolling update:
```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v2.0"
```

### 5.2 Quan sát flow trong Terminal B

```
[PRE-FLIGHT] ping OK → LB OK → Flask OK

── node3 (serial: 1) ──────────────────────────
[1/5] Remove node3 khỏi LB → nginx reload
[1/5] Drain 8s ...
[2/5] Backup webapp node3
[3/5] Deploy v2.0 → build image, restart container
[4/5] Health check → HTTP 200 ✓
[5/5] Add node3 trở lại LB → nginx reload
✅ node3 xong!

── node1 (serial: 1) ──────────────────────────
[1/5] Remove node1 khỏi LB → nginx reload
  (Terminal A lúc này chỉ thấy node3)
[3/5] Deploy v2.0 ...
[4/5] Health check → HTTP 200 ✓
[5/5] Add node1 trở lại LB → nginx reload
✅ node1 xong!

[FINAL] HTTP check qua LB → 200 OK ✓
ROLLING UPDATE HOÀN TẤT
```

### 5.3 Quan sát trong Terminal A (watch)

| Thời điểm | Terminal A thấy gì |
|-----------|------------------|
| Bình thường | server: node1 / node3 luân phiên |
| Đang update node3 | Chỉ thấy node1 |
| node3 xong, đang update node1 | Chỉ thấy node3 |
| Cả 2 xong | node1 / node3 luân phiên, version: v2.0 |

**Không có downtime** — Terminal A không bao giờ thấy lỗi.

### 5.4 Kiểm tra version trên browser

Mở **http://192.168.80.139** và F5 liên tục:
- Badge đổi từ **xanh dương (v1.0)** sang **xanh lá (v2.0)**
- SERVER_NAME vẫn thay đổi luân phiên node1/node3

---

## PHẦN 6: Demo Auto-Rollback (Bonus)

Để demo auto-rollback: SSH vào node3 và **xóa Flask container** trong khi playbook đang chạy ở bước health check.

**Terminal C** (chuẩn bị sẵn, chạy sau khi Terminal B báo "Drain 8s"):
```bash
ssh vagrant@192.168.80.141 'docker rm -f flask_app'
```

Ansible sẽ tự động:
1. Health check fail (6 lần × 5s = 30s)
2. Chạy rescue block
3. Restore backup → restart Flask v1.0
4. Add node3 trở lại LB
5. Fail playbook với thông báo rõ ràng

```
FAILED! => ❌ node3 FAIL! Da tu dong rollback.
           Kiem tra log: docker logs flask_app
```

---

## PHẦN 7: Rollback về v1.0

```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v1.0"
```

---

## Tổng hợp các lệnh thường dùng

```bash
# Deploy toàn bộ
ansible-playbook playbooks/site.yml

# Health check
ansible-playbook playbooks/healthcheck.yml

# Rolling update lên v2.0
ansible-playbook playbooks/rolling_update.yml -e "webapp_app_version=v2.0"

# Rollback về v1.0
ansible-playbook playbooks/rolling_update.yml -e "webapp_app_version=v1.0"

# Backup thủ công
ansible-playbook playbooks/backup.yml

# Chỉ deploy Flask (không build lại image)
ansible-playbook playbooks/site.yml --tags webapp

# Chỉ reload Nginx LB
ansible-playbook playbooks/site.yml --tags nginx
```

---

## Xử lý lỗi thường gặp

**Lỗi: `node3 unreachable`**
```bash
# Kiểm tra SSH
ssh vagrant@192.168.80.141
# Kiểm tra IP đúng chưa
ansible node3 -m setup -a "filter=ansible_default_ipv4"
```

**Lỗi: `community.docker not found`**
```bash
ansible-galaxy collection install -r requirements.yml --force
```

**Lỗi: `Nginx LB KHONG chay` khi chạy rolling_update.yml**
```bash
# Deploy lại nginx trước
ansible-playbook playbooks/site.yml --tags nginx
```

**Lỗi: MySQL connection refused từ Flask**
```bash
# Kiểm tra MySQL container
ansible node2 -m shell -a "docker ps | grep mysql"
# Kiểm tra port 3306
ansible node2 -m wait_for -a "host=127.0.0.1 port=3306 timeout=10"
```
