# Hướng dẫn Kiểm thử (Testing) Hệ thống Ansible

## Yêu cầu
- Đã clone project về và cài đặt môi trường xong (xem `docs/Setup.md`).
- Máy Control Node (máy chạy Ansible) đã sẵn sàng.
- 2 máy ảo `node1` (Web - `192.168.80.139`) và `node2` (DB - `192.168.80.140`) đang chạy bình thường (`vagrant status` báo running).

---

## Bước 1 — Cài đặt Dependencies (Ansible Galaxy)

**Mục đích:** Đảm bảo các thư viện mở rộng (collections) cần thiết cho project đã được cài.

```bash
ansible-galaxy collection install -r requirements.yml
```

**Kết quả đúng:**
```text
Starting galaxy collection install process
...
Nothing to do. All requested collections are already installed.
(Hoặc: was installed successfully)
```

---

## Bước 2 — Test Dynamic Inventory

**Mục đích:** Kiểm tra script Python đọc danh sách host tự động có hoạt động đúng không.

**Lệnh 1: Test script sinh JSON**
```bash
python3 inventories/dynamic_inventory.py --list
```
**Kết quả đúng:** Ra một chuỗi JSON chứa danh sách group `web`, `db` và `_meta`.

**Lệnh 2: Test Ansible đọc file Inventory**
```bash
ansible -i inventories/dynamic_inventory.py all --list-hosts
```
**Kết quả đúng:**
```text
  hosts (2):
    node1
    node2
```

---

## Bước 3 — Triển khai hệ thống (Deploy) lần đầu

**Mục đích:** Đẩy toàn bộ hạ tầng (Docker, MySQL, Flask, Nginx) lên 2 node. Bắt buộc chạy bước này trước khi test các tính năng sau.

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```
*(Nhập mật khẩu vault khi được hỏi)*

**Kết quả đúng:**
- Terminal chạy qua các task xanh (OK) hoặc vàng (Changed), không có dòng FAILED đỏ nào.
- Mở trình duyệt truy cập `http://192.168.80.139` thấy giao diện web "Ansible IAC Project" đang kết nối thành công tới Database.

---

## Bước 4 — Test Tags & Dry-run (Check mode)

**Mục đích:** Chạy thử kịch bản an toàn, chỉ chạy 1 phần cụ thể mà không làm thay đổi hệ thống thật.

```bash
ansible-playbook playbooks/site.yml --tags webapp --check --ask-vault-pass
```

**Kết quả đúng:**
- Playbook chỉ chạy các task có gắn tag `webapp` (bỏ qua phần cài Docker, MySQL...).
- Trạng thái các task chủ yếu là `ok` hoặc `skipping`. Hệ thống thực tế không bị thay đổi.

---

## Bước 5 — Test tính năng Backup

**Mục đích:** Tạo bản sao lưu mã nguồn Web và dữ liệu Database trước khi xảy ra sự cố.

```bash
ansible-playbook playbooks/backup.yml --ask-vault-pass
```

**Kết quả đúng:** Terminal chạy thành công. Để chắc chắn 100%, kiểm tra trực tiếp trên máy ảo:

**Kiểm tra trên node1 (Web):**
```bash
ssh vagrant@192.168.80.139 "sudo ls -la /opt/backups/webapp/"
```
*Kết quả:* Thấy file nén `webapp_xxxx.tar.gz` (vài KB) và symlink `latest.tar.gz` trỏ đúng vào nó.

**Kiểm tra trên node2 (DB):**
```bash
ssh vagrant@192.168.80.140 "sudo ls -la /opt/backups/mysql/"
```
*Kết quả:* Thấy file `mysql_xxxx.sql.gz` và symlink `latest.sql.gz`.

---

## Bước 6 — Test Health Check & Rollback (Giả lập sự cố)

**Mục đích:** Đánh sập web để thử phản ứng của hệ thống và tính năng tự động phục hồi.

**1. Đánh sập Web:**
```bash
ssh vagrant@192.168.80.139 "sudo docker stop flask_app"
```
*(F5 trình duyệt: Web sẽ quay đều hoặc báo lỗi 502).*

**2. Chạy Health Check xem hệ thống có phát hiện lỗi không:**
```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```
**Kết quả đúng:** Terminal báo **FAILED** (chữ đỏ) ở task "Assert Flask container dang chay" và Summary hiển thị `Flask container : FAIL`.

**3. Chạy Rollback "Cứu hộ":**
```bash
ansible-playbook playbooks/rollback.yml --ask-vault-pass
```
**Kết quả đúng:** Playbook giải nén file backup và start lại container thành công.

**4. Xác nhận hệ thống sống lại:**
```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```
**Kết quả đúng:** Summary in ra tất cả đều **OK** xanh lè. F5 trình duyệt web hiển thị lại bình thường!
