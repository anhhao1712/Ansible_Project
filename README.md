# Ansible_Project
## 🗺️ Luồng hoạt động hệ thống

```
┌────────────────────────────────────┐
                    │            CONTROL NODE            │
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
  │     docker/     │      │ nginx_service/  │      │   security/     │
  │─────────────────│      │─────────────────│      │─────────────────│
  │tasks/main.yml   │      │tasks/main.yml   │      │tasks/main.yml   │
  │tasks/install.yml│      │handlers/main.yml│      │UFW, SSH         │
  │                 │      │templates/       │      │hardening        │
  │                 │      │vars/main.yml    │      │                 │
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
│   │   ├── handlers/
│   │   │   └── main.yml ............ [Người B] (P3) - Lệnh khởi động lại/reload Nginx khi cần.
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

## ⚙️ Yêu cầu môi trường (Prerequisites)
* **Máy thật (Host):** Windows 10/11 (RAM ≥ 8GB), cài sẵn VMware Workstation, Vagrant & Vagrant VMware Utility.
* **Máy điều khiển (Control Node):** Ubuntu 20.04/22.04 (RAM ≥ 2GB), kết nối mạng NAT/Bridged.
> 💡 *Xem chi tiết yêu cầu phần cứng và hướng dẫn cài đặt từng bước tại: [`docs/Setup.md`](docs/Setup.md)*
