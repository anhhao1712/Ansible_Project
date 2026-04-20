# Hướng dẫn chạy web

## Yêu cầu
- Đã clone project về và cài đặt môi trường xong (xem `docs/Setup.md`)
- ControlNode đã cài Ansible
- node1 (`192.168.80.139`) và node2 (`192.168.80.140`) đang chạy

---

## Bước 1 — Test kết nối

```bash
ansible all -m ping
```

Kết quả đúng:
```
node1 | SUCCESS => pong
node2 | SUCCESS => pong
```

---

## Bước 2 — Chạy playbook

```bash
ansible-playbook playbooks/site.yml
```

Lần đầu chạy mất khoảng **10-15 phút** do cần build image Flask và pull các image Docker.

Kết quả thành công:
```
PLAY RECAP
node1 : ok=33  changed=6  failed=0
node2 : ok=25  changed=3  failed=0
```

---

## Bước 3 — Mở trình duyệt

```
http://192.168.80.139
```

Trang web hiển thị:
- Danh sách server đọc từ MySQL
- Lịch sử deploy logs từ MySQL

---

## Lỗi thường gặp

**502 Bad Gateway** — Nginx chưa nhận đúng IP Flask:
```bash
ssh vagrant@192.168.80.139
sudo tee /tmp/nginx_conf/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://172.17.0.2:5000;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
EOF
sudo docker restart webserver
```

**Bảng data trống / lỗi cryptography** — thiếu package trong Flask:
```bash
ssh vagrant@192.168.80.139
sudo docker exec flask_app pip install cryptography \
  -i https://mirrors.aliyun.com/pypi/simple/ \
  --trusted-host mirrors.aliyun.com
sudo docker restart flask_app
```

**Image pull bị treo** — thêm Docker mirror:
```bash
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": ["https://mirrors.aliyun.com"],
  "dns": ["8.8.8.8", "1.1.1.1"]
}
EOF
sudo systemctl restart docker
```
