markdown# 🧪 Testing Guide — Ansible IAC Project

Hướng dẫn kiểm thử toàn bộ hệ thống Ansible, từ deploy đến backup và rollback.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Bước 1 — Cài Dependencies](#bước-1--cài-dependencies-ansible-galaxy)
- [Bước 2 — Mã hóa Vault](#bước-2--mã-hóa-secrets-với-ansible-vault)
- [Bước 3 — Deploy lần đầu](#bước-3--triển-khai-hệ-thống-deploy-lần-đầu)
- [Bước 4 — Test Tags & Dry-run](#bước-4--test-tags--dry-run-check-mode)
- [Bước 5 — Test Backup](#bước-5--test-tính-năng-backup)
- [Bước 6 — Test Health Check & Rollback](#bước-6--test-health-check--rollback-giả-lập-sự-cố)

---

## ✅ Prerequisites

Trước khi bắt đầu, đảm bảo:

| Yêu cầu | Chi tiết |
|---|---|
| Control Node | Đã cài Ansible, sẵn sàng chạy playbook |
| node1 (Web) | `192.168.80.139` — trạng thái `running` |
| node2 (DB) | `192.168.80.140` — trạng thái `running` |

```bash
vagrant status
```

---

## Bước 1 — Cài Dependencies (Ansible Galaxy)

> **Mục đích:** Đảm bảo các collections cần thiết đã được cài đầy đủ trước khi chạy playbook.

```bash
ansible-galaxy collection install -r requirements.yml
```

**✔️ Kết quả đúng:**
Starting galaxy collection install process
...
Nothing to do. All requested collections are already installed.

---

## Bước 2 — Mã hóa Secrets với Ansible Vault

> **Mục đích:** Bảo vệ thông tin nhạy cảm (database password, credentials) bằng cách mã hóa trước khi dùng.

**1. Kiểm tra nội dung file trước khi mã hóa:**
```bash
cat vault/secrets.yml
```
*Thấy plaintext: `db_root_password`, `db_name`, `db_user`.*

**2. Mã hóa file:**
```bash
ansible-vault encrypt vault/secrets.yml
```
*(Nhập và xác nhận mật khẩu vault khi được yêu cầu)*

**3. Xác nhận đã mã hóa thành công:**
```bash
cat vault/secrets.yml
```

**✔️ Kết quả đúng** — dòng đầu hiển thị:
$ANSIBLE_VAULT;1.1;AES256

**4. Lưu vault password vào file để tiện dùng lại:**
```bash
echo "your_vault_password" > vault/.vault_pass
chmod 600 vault/.vault_pass
```

---

## Bước 3 — Triển khai Hệ thống (Deploy lần đầu)

> **Mục đích:** Đẩy toàn bộ hạ tầng (Docker, MySQL, Flask, Nginx) lên 2 node. **Bắt buộc chạy trước** khi test các bước tiếp theo.

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

**✔️ Kết quả đúng:**
- Tất cả task hiển thị `ok` (xanh) hoặc `changed` (vàng), không có `FAILED` đỏ nào.
- Truy cập `http://192.168.80.139` → thấy giao diện **"Ansible IAC Project"** kết nối thành công tới Database.

---

## Bước 4 — Test Tags & Dry-run (Check mode)

> **Mục đích:** Chạy thử an toàn — chỉ thực thi một phần playbook mà **không thay đổi hệ thống thật**.

```bash
ansible-playbook playbooks/site.yml --tags webapp --check --ask-vault-pass
```

**✔️ Kết quả đúng:**
- Chỉ chạy các task có tag `webapp` (bỏ qua Docker, MySQL...).
- Trạng thái task chủ yếu là `ok` hoặc `skipping`.
- Hệ thống thực tế **không bị thay đổi**.

---

## Bước 5 — Test Tính năng Backup

> **Mục đích:** Tạo bản sao lưu mã nguồn Web và dữ liệu Database phòng khi xảy ra sự cố.

```bash
ansible-playbook playbooks/backup.yml --ask-vault-pass
```

Sau khi terminal báo thành công, kiểm tra trực tiếp trên từng node:

**Kiểm tra node1 (Web):**
```bash
ssh vagrant@192.168.80.139 "sudo ls -la /opt/backups/webapp/"
```
*✔️ Thấy file `webapp_xxxx.tar.gz` và symlink `latest.tar.gz` trỏ đúng vào nó.*

**Kiểm tra node2 (DB):**
```bash
ssh vagrant@192.168.80.140 "sudo ls -la /opt/backups/mysql/"
```
*✔️ Thấy file `mysql_xxxx.sql.gz` và symlink `latest.sql.gz`.*

---

## Bước 6 — Test Health Check & Rollback (Giả lập sự cố)

> **Mục đích:** Giả lập web bị sập, kiểm tra hệ thống có phát hiện lỗi và tự phục hồi được không.

### 6.1 — Đánh sập Web
```bash
ssh vagrant@192.168.80.139 "sudo docker stop flask_app"
```
*F5 trình duyệt → web báo lỗi 502 hoặc không phản hồi.*

### 6.2 — Chạy Health Check
```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```
**✔️ Kết quả đúng:** Task `Assert Flask container dang chay` báo **FAILED** (đỏ), summary hiển thị:
Flask container : FAIL

### 6.3 — Chạy Rollback
```bash
ansible-playbook playbooks/rollback.yml --ask-vault-pass
```
*✔️ Playbook giải nén file backup và start lại container thành công.*

### 6.4 — Xác nhận hệ thống đã phục hồi
```bash
ansible-playbook playbooks/healthcheck.yml --ask-vault-pass
```
**✔️ Kết quả đúng:** Tất cả task đều `OK` (xanh). F5 trình duyệt → web hiển thị lại bình thường.
