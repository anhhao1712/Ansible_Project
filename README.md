# Ansible_Project
## 🗺️ Luồng hoạt động hệ thống

```
                    ┌────────────────────────────────────┐
                    │              CONTROL NODE          │
                    │                                    │
                    │  ┌───────────┐  ┌───────────┐      │
                    │  │ansible.cfg│  │ hosts.ini │      │
                    │  │cấu hình   │  │danh sách  │      │
                    │  │toàn cục   │  │IP máy     │      │
                    │  └───────────┘  └───────────┘      │
                    │  ┌───────────┐  ┌───────────┐      │
                    │  │secrets.yml│  │group_vars/│      │
                    │  │vault - mật│  │biến dùng  │      │
                    │  │khẩu       │  │chung      │      │
                    │  └───────────┘  └───────────┘      │
                    └──────────────────┬─────────────────┘
                                       │ ansible-playbook
                                       ▼
                          ┌────────────────────────┐
                          │   playbooks/site.yml   │
                          │  điều phối các roles   │
                          └────────────┬───────────┘
                                       │ import_role
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
  │    docker/      │      │ nginx_service/  │      │   security/     │
  │─────────────────│      │─────────────────│      │─────────────────│
  │tasks/main.yml   │      │tasks/main.yml   │      │tasks/main.yml   │
  │tasks/install.yml│      │templates/       │      │UFW, SSH         │
  │                 │      │vars/main.yml    │      │hardening        │
  │Cài Docker Engine│      │Deploy web Nginx │      │Cấu hình bảo mật │
  └─────────────────┘      └─────────────────┘      └─────────────────┘
              │                        │                        │
              └────────────────────────┼────────────────────────┘
                                       │ SSH (port 22)
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
              ┌─────────────────┐         ┌─────────────────┐
              │     Node 1      │         │     Node 2      │
              │─────────────────│         │─────────────────│
              │ Ubuntu          │         │ Ubuntu          │
              │ OpenSSH Server  │         │ OpenSSH Server  │
              │ Python 3        │         │ Python 3        │
              └─────────────────┘         └─────────────────┘
                         │                           │
                         └─────────────┬─────────────┘
                                       │ kết quả / changed
                                       ▼
                          ┌────────────────────────┐
                          │  ansible all -m ping   │
                          │  → SUCCESS / pong      │
                          └────────────────────────┘

```








```
ANSIBLE_IAC_PROJECT/
├── inventories/
│   └── hosts.ini ................... [Người A] (P1) - Bản đồ địa chỉ các máy server.
├── playbooks/
│   └── site.yml .................... [Người C] (P4) - Nút nguồn tổng, bấm là chạy cả dự án.
├── roles/
│   ├── docker/
│   │   └── tasks/
│   │       ├── main.yml ............ [Người A] (P2) - Điều hướng cài đặt Docker.
│   │       └── install.yml ......... [Người A] (P2) - Các lệnh cài Engine & SDK Python.
│   ├── nginx_service/
│   │   ├── tasks/
│   │   │   └── main.yml ............ [Người B] (P3) - Lệnh kéo Image & chạy Container Nginx.
│   │   ├── templates/
│   │   │   └── index.html.j2 ....... [Người B] (P3) - Trang web hiển thị (có biến động).
│   │   └── vars/
│   │       └── main.yml ............ [Người B] (P3) - Biến riêng cho Nginx (tên container, port).
│   └── security/
│       └── tasks/
│           └── main.yml ............ [Người C] (P3) - Cấu hình "tấm khiên" Firewall UFW.
├── group_vars/
│   └── all.yml ..................... [Người C] (P2) - Kho chứa biến chung cho toàn dự án.
├── vault/
│   └── secrets.yml ................. [Người A] (P2) - Két sắt mã hóa mật khẩu sudo.
├── ansible.cfg ..................... [Người A] (P1) - Cài đặt "luật chơi" cho Ansible.
└── README.md ....................... [Người A] (P4) - Sách hướng dẫn sử dụng đồ án.
```


# 🛠️ Hướng Dẫn Cài Đặt Môi Trường

> **Giai đoạn 1 — Chuẩn bị hạ tầng cho dự án Ansible**  
> Đọc kỹ và thực hiện đúng thứ tự. Mỗi thành viên cần tự cài trên máy ảo của mình.

---

## 📋 Tổng quan kiến trúc

```
┌─────────────────────┐         SSH          ┌──────────────────────┐
│   Control Node      │ ──────────────────►  │   Node 1 (Managed)   │
│  (máy ra lệnh)      │                      └──────────────────────┘
│                     │         SSH          ┌──────────────────────┐
│  • Ansible          │ ──────────────────►  │   Node 2 (Managed)   │
│  • sshpass          │                      └──────────────────────┘
└─────────────────────┘
```

---

## 🖥️ Phần 1 — Cài đặt trên các máy Managed Node (Node 1 & Node 2)

> Thực hiện **trực tiếp trên terminal** của từng máy ảo Ubuntu.

### Bước 1 — Cài đặt OpenSSH Server

Ansible giao tiếp qua SSH, nên máy managed node **bắt buộc** phải có SSH.

```bash
sudo apt update
sudo apt install openssh-server -y
```

### Bước 2 — Kích hoạt dịch vụ SSH

Đảm bảo SSH tự động khởi động cùng hệ thống:

```bash
sudo systemctl enable --now ssh
```

Kiểm tra SSH đang chạy:

```bash
sudo systemctl status ssh
```

> ✅ Kết quả mong muốn: dòng trạng thái hiển thị `active (running)`

### Bước 3 — Cấu hình Firewall

Mở cổng 22 để cho phép kết nối SSH từ Control Node:

```bash
sudo ufw allow ssh
sudo ufw reload
```

---

## 💻 Phần 2 — Cài đặt trên máy Control Node

> Thực hiện trên **máy dùng để ra lệnh** (Control Node).

### Bước 1 — Cài đặt Ansible và sshpass

`sshpass` cho phép Ansible đăng nhập bằng mật khẩu tự động (thay vì SSH key).

```bash
sudo apt update
sudo apt install ansible sshpass -y
```

Kiểm tra cài đặt thành công:

```bash
ansible --version
```

### Bước 2 — Cấu hình Inventory

File inventory xác định danh sách các máy mà Ansible sẽ quản lý.  
Dùng lệnh sau để chỉnh sửa:

```bash
nano inventories/hosts.ini
```

Cập nhật nội dung theo mẫu dưới đây, **thay IP thực tế của máy bạn vào**:

```ini
[web]
node1 ansible_host=192.168.x.x   # ← Điền IP thực tế của Node 1
node2 ansible_host=192.168.y.y   # ← Điền IP thực tế của Node 2

[web:vars]
ansible_user=ubuntu
ansible_ssh_pass='0'              # Mật khẩu PHẢI để trong dấu nháy đơn
ansible_become=true
ansible_become_method=sudo
ansible_become_pass='0'
ansible_python_interpreter=/usr/bin/python3
```

> ⚠️ **Lưu ý quan trọng:**  
> - Mỗi thành viên nhóm có IP máy ảo **khác nhau** — không copy nguyên của người khác.  
> - Để tìm IP của máy ảo, chạy lệnh `ip a` trên máy đó.  
> - Giá trị `ansible_ssh_pass` và `ansible_become_pass` **bắt buộc** để trong dấu nháy đơn `' '`.

---

## 🚀 Phần 3 — Kiểm tra kết nối

Sau khi hoàn tất cả hai phần trên, đứng tại **thư mục gốc của dự án** trên Control Node và chạy:

```bash
ansible all -m ping
```

**Kết quả thành công** sẽ trông như sau:

```
node1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
node2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

> ❌ Nếu báo lỗi, hãy kiểm tra lại:
> - IP trong `hosts.ini` có đúng không?
> - SSH trên managed node có đang chạy không? (`sudo systemctl status ssh`)
> - Hai máy có ping được nhau không? (`ping 192.168.x.x`)

---

## 🔍 Tra cứu nhanh các lệnh thường dùng

| Mục đích | Lệnh |
|---|---|
| Kiểm tra IP máy | `ip a` |
| Kiểm tra SSH đang chạy | `sudo systemctl status ssh` |
| Xem version Ansible | `ansible --version` |
| Ping tất cả node | `ansible all -m ping` |
| Ping nhóm `web` | `ansible web -m ping` |
| Xem danh sách inventory | `ansible-inventory --list` |
