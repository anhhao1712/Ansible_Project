# Hướng dẫn Kiểm thử (Testing) Hệ thống Ansible v2

## Yêu cầu

* Đã clone project về và giải nén `Ansible_Project_v2.rar`.
* Máy Control Node (máy chạy Ansible) đã cài sẵn Ansible >= 2.14 và Python >= 3.9.
* Máy ảo `node1` (Web/LB - `192.168.80.139`) và `node2` (DB - `192.168.80.140`) đang chạy bình thường (`vagrant status` báo `running`).
* Máy ảo `node3` (Web - `192.168.80.141`) đã được clone từ node1 và đổi IP (xem `docs/ROLLING_UPDATE_DEMO.md` mục "Bước 0").

---

## Bước 1 — Cài đặt Dependencies (Ansible Galaxy)

**Mục đích:** Đảm bảo các thư viện mở rộng (collections) cần thiết cho project đã được cài đầy đủ trước khi chạy bất kỳ lệnh nào.

```bash
ansible-galaxy collection install -r requirements.yml
```

**Kết quả đúng:**

```
Starting galaxy collection install process
...
Nothing to do. All requested collections are already installed.
(Hoặc: was installed successfully)
```

---

## Bước 2 — Kiểm tra kết nối tới 3 Nodes

**Mục đích:** Xác nhận Ansible có thể SSH vào cả 3 máy ảo và chúng đang online trước khi deploy.

```bash
ansible all -m ping
```

**Kết quả đúng:**

```
node1 | SUCCESS => {"ping": "pong"}
node2 | SUCCESS => {"ping": "pong"}
node3 | SUCCESS => {"ping": "pong"}
```

> Nếu `node3` báo `UNREACHABLE`: kiểm tra lại IP (`ssh vagrant@192.168.80.141`) và đảm bảo VM đang chạy.

---

## Bước 3 — Test Dynamic Inventory

**Mục đích:** Kiểm tra script Python đọc danh sách host tự động có sinh đúng group và host không.

**Lệnh 1 — Test script sinh JSON:**

```bash
python3 inventories/dynamic_inventory.py --list
```

**Kết quả đúng:** Ra một chuỗi JSON chứa danh sách group `web` (node1, node3), `db` (node2), `lb` (node1) và `_meta`.

**Lệnh 2 — Test Ansible đọc file Inventory:**

```bash
ansible -i inventories/dynamic_inventory.py all --list-hosts
```

**Kết quả đúng:**

```
  hosts (3):
    node1
    node2
    node3
```

---

## Bước 4 — Triển khai hệ thống (Deploy) lần đầu

**Mục đích:** Đẩy toàn bộ hạ tầng (Docker, MySQL, Flask, Nginx Load Balancer) lên 3 node. **Bắt buộc chạy bước này trước khi test các tính năng sau.**

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

(Nhập mật khẩu vault khi được hỏi — mặc định: `vagrant`)

**Thứ tự deploy:**

| Play | Hosts | Nội dung |
|------|-------|---------|
| Play 1 | all | Kiểm tra biến global |
| Play 2 | node2 | Docker + MySQL 8.0 + Security |
| Play 3 | node1, node3 | Docker + Flask App (serial: 1) + Security |
| Play 4 | node1 | Nginx Load Balancer |

**Kết quả đúng:**

* Terminal chạy qua các task xanh (`ok`) hoặc vàng (`changed`), không có dòng `FAILED` đỏ nào.
* Mở trình duyệt truy cập `http://192.168.80.139` thấy giao diện "Ansible IAC Project" với badge **v1.0** màu xanh dương và bảng dữ liệu từ MySQL.

---

## Bước 5 — Kiểm tra Load Balancer Round-Robin

**Mục đích:** Xác nhận Nginx đang phân phối traffic đều đến cả node1 và node3.

```bash
for i in $(seq 1 8); do
  curl -s http://192.168.80.139/health | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d['server'])"
done
```

**Kết quả đúng:**

```
node1
node3
node1
node3
node1
node3
node1
node3
```

Server xen kẽ đều đặn giữa `node1` và `node3` → LB round-robin hoạt động đúng.

**Kiểm tra thêm — Xem config Nginx LB:**

```bash
ssh vagrant@192.168.80.139 "cat /tmp/nginx_conf/default.conf"
```

**Kết quả đúng:** Thấy block `upstream flask_cluster` chứa 2 dòng `server` trỏ về `192.168.80.139:5000` và `192.168.80.141:5000`.

---

## Bước 6 — Test Tags & Dry-run (Check mode)

**Mục đích:** Chạy thử kịch bản an toàn, chỉ chạy 1 phần cụ thể mà không làm thay đổi hệ thống thật.

```bash
ansible-playbook playbooks/site.yml --tags webapp --check --ask-vault-pass
```

**Kết quả đúng:**

* Playbook chỉ chạy các task có gắn tag `webapp` (bỏ qua phần cài Docker, MySQL, Nginx).
* Trạng thái các task chủ yếu là `ok` hoặc `skipping`. Hệ thống thực tế không bị thay đổi.

---

## Bước 7 — Test tính năng Backup

**Mục đích:** Tạo bản sao lưu mã nguồn Web và dữ liệu Database trước khi xảy ra sự cố.

```bash
ansible-playbook playbooks/backup.yml --ask-vault-pass
```

**Kết quả đúng:** Terminal chạy thành công. Để xác nhận, kiểm tra trực tiếp trên máy ảo:

**Kiểm tra trên node1 (Web):**

```bash
ssh vagrant@192.168.80.139 "sudo ls -la /opt/backups/webapp/"
```

**Kết quả:** Thấy file nén `webapp_YYYY-MM-DD_HHMM.tar.gz` và symlink `latest.tar.gz` trỏ đúng vào nó.

**Kiểm tra trên node2 (DB):**

```bash
ssh vagrant@192.168.80.140 "sudo ls -la /opt/backups/mysql/"
```

**Kết quả:** Thấy file `mysql_YYYY-MM-DD_HHMM.sql.gz` và symlink `latest.sql.gz`.

---

## Bước 8 — Test Health Check

**Mục đích:** Kiểm tra hệ thống monitoring tự phát hiện sự cố.

**1. Đánh sập Flask trên node1:**

```bash
ssh vagrant@192.168.80.139 "sudo docker stop flask_app"
```

(F5 trình duyệt: vẫn load được vì LB tự chuyển sang node3)

**2. Chạy Health Check:**

```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```

**Kết quả đúng:** Terminal báo `FAILED` (chữ đỏ) ở task "Assert Flask container dang chay" trên node1. Summary hiển thị:

```
Flask container : FAIL
Flask HTTP      : FAIL
```

**3. Khởi động lại Flask:**

```bash
ssh vagrant@192.168.80.139 "sudo docker start flask_app"
```

**4. Chạy Health Check lần nữa để xác nhận:**

```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```

**Kết quả đúng:** Tất cả đều `OK`. F5 trình duyệt thấy traffic trở lại phân phối cho cả node1 và node3.

---

## Bước 9 — Test Rolling Update (Zero-Downtime)

**Mục đích:** Nâng cấp Flask app từ v1.0 lên v2.0 mà không làm gián đoạn traffic người dùng.

**1. Mở 2 terminal song song.**

**Terminal A — Theo dõi traffic liên tục:**

```bash
watch -n 0.5 'curl -s http://192.168.80.139/health'
```

**Terminal B — Chạy rolling update:**

```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v2.0" --ask-vault-pass
```

**Kết quả đúng ở Terminal B:**

```
[PRE-FLIGHT] ping OK → LB OK → Flask OK trên cả 2 node

[ROLLING UPDATE] node3:
  [1/5] Remove node3 khỏi LB → nginx reload
  [1/5] Drain 8s ...
  [2/5] Backup webapp node3
  [3/5] Deploy v2.0 → build image, restart container
  [4/5] Health check HTTP 200 ✓
  [5/5] Add node3 trở lại LB → nginx reload
  ✅ node3 update xong!

[ROLLING UPDATE] node1: (tương tự)
  ✅ node1 update xong!

[FINAL] HTTP check qua LB → 200 OK
ROLLING UPDATE HOÀN TẤT
```

**Kết quả đúng ở Terminal A:** Không có lần nào báo lỗi hay timeout. Trong khi update node3, chỉ thấy `node1`. Trong khi update node1, chỉ thấy `node3`. Sau khi xong, hiển thị `"version": "v2.0"`.

**Kiểm tra trên browser:** Truy cập `http://192.168.80.139`, F5 liên tục → badge đổi từ **xanh dương (v1.0)** sang **xanh lá (v2.0)**.

---

## Bước 10 — Test Auto-Rollback

**Mục đích:** Xác nhận hệ thống tự động phát hiện deploy lỗi và phục hồi về trạng thái ổn định.

**1. Đảm bảo hệ thống đang chạy bình thường (bước 9 đã xong).**

**2. Mở 2 terminal song song.**

**Terminal A — Theo dõi traffic:**

```bash
watch -n 0.5 'curl -s http://192.168.80.139/health'
```

**Terminal B — Chạy rolling update:**

```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v2.0" --ask-vault-pass
```

**3. Ngay sau khi Terminal B hiển thị "[1/5] Drain 8s", chạy Terminal C:**

```bash
ssh vagrant@192.168.80.141 "sudo docker rm -f flask_app"
```

**Kết quả đúng ở Terminal B:** Sau 30s (6 lần retry × 5s), playbook kích hoạt auto-rollback:

```
FAILED - RETRYING: HTTP GET /health (6 retries left)
...
[AUTO-ROLLBACK] Health check FAIL! Rollback node3...
[ROLLBACK] Stop container lỗi
[ROLLBACK] Khôi phục webapp từ backup
[ROLLBACK] Restart Flask container cũ
[ROLLBACK] Add lại node3 vào LB
[ROLLBACK] Reload LB sau rollback

FAILED! => ❌ node3 FAIL! Da tu dong rollback.
           Kiem tra log: docker logs flask_app
```

**Kết quả đúng ở Terminal A:** Không có lỗi nào trong suốt quá trình. LB đã tự chuyển traffic sang node1 khi node3 bị lỗi và trở lại bình thường sau rollback.

**4. Xác nhận hệ thống ổn định sau rollback:**

```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```

**Kết quả đúng:** Tất cả `OK`. node3 đang chạy lại phiên bản trước đó.

---

## Bước 11 — Rollback toàn bộ về v1.0

**Mục đích:** Đưa toàn bộ hệ thống trở về phiên bản ổn định ban đầu.

```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v1.0" --ask-vault-pass
```

**Kết quả đúng:** Cả node1 và node3 đều về v1.0. Trình duyệt hiển thị badge **xanh dương (v1.0)**.

---

## Tổng hợp kết quả kiểm thử

| # | Tính năng | Lệnh chính | Kết quả mong đợi |
|---|-----------|-----------|-----------------|
| 1 | Dependencies | `ansible-galaxy install` | All installed |
| 2 | Kết nối nodes | `ansible all -m ping` | 3 nodes pong |
| 3 | Dynamic Inventory | `dynamic_inventory.py --list` | JSON đúng group |
| 4 | Deploy lần đầu | `site.yml` | Web hoạt động |
| 5 | Load Balancer | `curl /health` × 8 | node1/node3 luân phiên |
| 6 | Tags & Dry-run | `--tags webapp --check` | Không thay đổi thật |
| 7 | Backup | `backup.yml` | File .tar.gz + .sql.gz |
| 8 | Health Check | `healthcheck.yml` | Phát hiện FAIL chính xác |
| 9 | Rolling Update | `rolling_update.yml` | Zero-downtime, v2.0 OK |
| 10 | Auto-Rollback | Phá Flask mid-deploy | Tự rollback, LB ổn định |
| 11 | Rollback v1.0 | `rolling_update.yml -e v1.0` | Hệ thống về v1.0 |
