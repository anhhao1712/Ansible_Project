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
Ansible_Project/
├── .github/
│   └── workflows/
│       └── deploy.yml          # [MỚI] CI/CD GitHub Actions
│
├── ansible.cfg
├── requirements.yml            # [MỚI] Ansible Galaxy dependencies
├── README.md
│
├── docs/
│   ├── Setup.md
│
├── inventories/
│   ├── hosts.ini
│   ├── dynamic_inventory.py    # [MỚI] Dynamic Inventory script
│   ├── dynamic_inventory.yml   # [MỚI] Inventory plugin config
│   └── group_vars/
│       └── all.yml
│
├── playbooks/
│   ├── site.yml                # [SỬA] thêm serial, tags
│   ├── backup.yml              # [MỚI] Backup playbook
│   ├── rollback.yml            # [MỚI] Rollback playbook
│   └── healthcheck.yml         # [MỚI] Health Check playbook
│
├── roles/
│   ├── backup/                 # [MỚI] Backup & Rollback role
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── vars/
│   │       └── main.yml
│   │
│   ├── healthcheck/            # [MỚI] Health Check role
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── vars/
│   │       └── main.yml
│   │
│   ├── docker/
│   │   └── tasks/
│   │       ├── install.yml     # [SỬA] thêm tags
│   │       └── main.yml
│   │
│   ├── mysql/
│   │   ├── files/
│   │   │   └── seed_data.sql
│   │   ├── tasks/
│   │   │   └── main.yml        # [SỬA] thêm tags
│   │   └── vars/
│   │       └── main.yml
│   │
│   ├── nginx_service/
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── tasks/
│   │   │   └── main.yml        # [SỬA] thêm tags
│   │   ├── templates/
│   │   │   └── nginx.conf.j2
│   │   └── vars/
│   │       └── main.yml
│   │
│   ├── security/
│   │   └── tasks/
│   │       └── main.yml
│   │
│   └── webapp/
│       ├── files/
│       │   ├── app.py
│       │   ├── Docker
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
