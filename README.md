# Ansible_Project

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
