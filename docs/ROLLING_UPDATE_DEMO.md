# Rolling Update Demo Guide

Tài liệu hướng dẫn demo **Zero-Downtime Rolling Update** với Ansible + Nginx LB.

---

## Kiến trúc sau khi setup

```
[Người dùng / Browser]
        │
        ▼ port 80
  node1 — Nginx LB (192.168.80.139)
        │
        ├──► node1:5000  Flask App (192.168.80.139)
        └──► node3:5000  Flask App (192.168.80.141)
                │
                ▼ port 3306
        node2 — MySQL (192.168.80.140)
```

---

## Bước 0: Chuẩn bị (1 lần duy nhất)

### 0.1 Clone VM node1 thành node3

Trong VMware/VirtualBox:
1. Clone node1 → đặt tên **node3**
2. Đổi IP thành `192.168.80.141` (sửa trong `/etc/netplan/` hoặc `/etc/network/interfaces`)
3. Đảm bảo SSH với user `vagrant / vagrant` vẫn hoạt động

### 0.2 Deploy toàn bộ hệ thống lần đầu

```bash
# Deploy MySQL + Flask (node1, node3) + Nginx LB (node1)
ansible-playbook playbooks/site.yml

# Kiểm tra tất cả đều healthy
ansible-playbook playbooks/healthcheck.yml
```

### 0.3 Kiểm tra LB hoạt động

```bash
# Refresh liên tục để thấy SERVER_NAME thay đổi node1 <-> node3
for i in $(seq 1 10); do
  curl -s http://192.168.80.139/health | python3 -m json.tool
  sleep 0.5
done
```

Kết quả mong đợi: `"server"` xen kẽ giữa `node1` và `node3` → LB round-robin đang hoạt động.

---

## Bước 1: Demo Rolling Update (v1.0 → v2.0)

### Mở 2 terminal song song

**Terminal A — Watch traffic liên tục:**
```bash
watch -n 0.5 'curl -s http://192.168.80.139/health'
```

**Terminal B — Chạy rolling update:**
```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v2.0"
```

### Quan sát flow

```
Terminal B sẽ hiển thị:
[PRE-FLIGHT] → ping OK, LB OK, Flask OK

[ROLLING UPDATE] node3 (serial: 1)
  [1/5] Remove node3 khỏi LB → reload nginx
  [1/5] Drain 8s ...
  [2/5] Backup webapp node3
  [3/5] Deploy v2.0 lên node3 (build Docker image, restart container)
  [4/5] Health check node3 → OK
  [5/5] Add node3 trở lại LB → reload nginx
  ✅ node3 update xong!

[ROLLING UPDATE] node1 (serial: 1)
  [1/5] Remove node1 khỏi LB → reload nginx
  ... (tương tự) ...
  ✅ node1 update xong!

[FINAL] HTTP check qua LB → 200 OK
  → ROLLING UPDATE HOÀN TẤT
```

**Terminal A (watch) sẽ:**
- Trong khi update node3: chỉ thấy `"server": "node1"` → node3 đã bị remove
- Sau khi node3 xong: thấy cả node1 và node3 luân phiên
- Trong khi update node1: chỉ thấy `"server": "node3"` → node1 đã bị remove
- Sau khi xong: cả 2 node trở lại, version = `v2.0`

**Mở browser:** `http://192.168.80.139` → F5 liên tục → thấy badge version đổi màu từ xanh dương (v1.0) → xanh lá (v2.0)

---

## Bước 2: Demo Auto-Rollback

Để test tính năng auto-rollback, có thể dùng cách sau:

```bash
# Truyền version không tồn tại → Flask vẫn start nhưng có thể dùng
# để demo bằng cách break app trước khi chạy
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v_broken"
```

Hoặc test thực tế hơn: SSH vào node3, stop Flask sau khi nó được remove khỏi LB:

```bash
# Trên node3
docker stop flask_app
```

Ansible sẽ:
1. Deploy xong
2. Health check → FAIL (Flask không response)
3. Tự động rollback: restore backup → restart Flask v1.0 → add lại vào LB
4. Playbook fail với thông báo rõ ràng

---

## Bước 3: Rollback toàn bộ về v1.0

```bash
ansible-playbook playbooks/rolling_update.yml \
  -e "webapp_app_version=v1.0"
```

---

## Các lệnh hữu ích khi demo

```bash
# Xem log Nginx LB
ssh vagrant@192.168.80.139 'docker logs webserver --tail 20 -f'

# Xem log Flask node1
ssh vagrant@192.168.80.139 'docker logs flask_app --tail 20 -f'

# Xem log Flask node3
ssh vagrant@192.168.80.141 'docker logs flask_app --tail 20 -f'

# Check config LB hiện tại
ssh vagrant@192.168.80.139 'cat /tmp/nginx_conf/default.conf'

# Xem upstream đang active
ssh vagrant@192.168.80.139 'docker exec webserver nginx -T 2>/dev/null | grep server'
```

---

## Giải thích kỹ thuật

| Bước | Ansible module | Mục đích |
|------|---------------|---------|
| Remove khỏi LB | `template` + `delegate_to` | Render lại `nginx_lb.conf.j2` với `lb_skip_hosts`, delegate sang node LB |
| Reload LB | `shell: docker exec nginx -s reload` | Graceful reload — không ngắt kết nối đang active |
| Drain | `pause: seconds: 8` | Chờ request cũ xử lý xong |
| Deploy | `include_role: webapp` | Build image mới, restart container với version mới |
| Health check | `uri` + `retries` | 6 lần, mỗi 5s — tổng 30s timeout |
| Auto-rollback | `block/rescue` | Rescue block chạy tự động khi health check fail |
| Add lại LB | `template` + `delegate_to` | Render lại config đầy đủ, reload nginx |
