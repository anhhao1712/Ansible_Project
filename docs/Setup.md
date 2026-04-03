# 🛠️ Hướng dẫn Cài đặt & Cấu hình Môi trường (Setup Guide)

Tài liệu này hướng dẫn chi tiết từng bước để thiết lập môi trường ảo hóa và cấu hình Ansible từ con số 0.

---

## 🪟 Phần 1 — Chuẩn bị trên máy Host (Windows)

> Thực hiện trên máy tính Windows thật của bạn. Mục tiêu là cài đặt các công cụ ảo hóa để tạo Managed Nodes.

### Bước 1 — Tải và cài đặt phần mềm lõi
1. **VMware Workstation / Player**: Đảm bảo máy bạn đã cài đặt sẵn phần mềm ảo hóa này.
2. **Vagrant**: Tải file `.msi` (bản Windows amd64) tại [🔗 Trang chủ Vagrant](https://developer.hashicorp.com/vagrant/docs/providers/vmware/vagrant-vmware-utility) và cài đặt (Next -> Finish).
3. **Vagrant VMware Utility**: Tải file `.msi` tương ứng tại [🔗 Trang tải Utility](https://developer.hashicorp.com/vagrant/docs/providers/vmware/vagrant-vmware-utility) và cài đặt. (Bắt buộc phải có công cụ này để Vagrant kết nối được với VMware).

### Bước 2 — Cài đặt Plugin và Khởi tạo máy ảo
Mở **PowerShell (Run as Administrator)** và thực hiện các lệnh sau:

```powershell
# Cài đặt plugin giao tiếp giữa Vagrant và VMware
vagrant plugin install vagrant-vmware-desktop

# Di chuyển đến thư mục chứa file Vagrantfile của dự án
cd D:\Đường_dẫn_tới_thư_mục_chứa_Vagrantfile\

# Khởi tạo và bật các máy ảo Managed Nodes
vagrant up
```

---

## 🖥️ Phần 2 — Cài đặt trên các máy Managed Node (Node 1 & Node 2)

> Thực hiện **trực tiếp trên terminal** của từng máy ảo Ubuntu (Managed Nodes).

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

> ✅ **Kết quả mong muốn:** dòng trạng thái hiển thị `active (running)`

### Bước 3 — Cấu hình Firewall

Mở cổng 22 để cho phép kết nối SSH từ Control Node:

```bash
sudo ufw allow ssh
sudo ufw reload
```

---

## 💻 Phần 3 — Cài đặt trên máy Control Node

> Thực hiện trên **máy dùng để ra lệnh** (Control Node / Ubuntu).

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
ansible_ssh_pass='0'             # Mật khẩu PHẢI để trong dấu nháy đơn
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

## 🚀 Phần 4 — Kiểm tra kết nối

Sau khi hoàn tất cả các phần trên, đứng tại **thư mục gốc của dự án** trên Control Node và chạy:

```bash
ansible all -m ping
```

**Kết quả thành công** sẽ trông như sau:

```json
node1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
node2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

---

## 🔧 Phần 5 — Xử lý sự cố thường gặp (Troubleshooting)

> Nếu trong quá trình setup hoặc chạy lệnh gặp lỗi, hãy sử dụng các lệnh dưới đây để kiểm tra và khắc phục.

### 1. Khi Vagrant gặp sự cố (Trên Windows PowerShell)

- **Kiểm tra trạng thái các máy ảo:**
  ```powershell
  vagrant status
  ```
  *(Giúp xác định máy ảo đang chạy `running`, đang tắt `poweroff` hay chưa tạo `not created`).*

- **Khởi động lại máy ảo (Khi bị treo hoặc không nhận IP):**
  ```powershell
  vagrant reload
  ```

- **Xóa hoàn toàn máy ảo để làm lại từ đầu (Khi lỗi quá nặng):**
  ```powershell
  vagrant destroy -f
  # Sau đó chạy lại lệnh: vagrant up
  ```

- **Xem log chi tiết nếu lệnh `vagrant up` báo lỗi đỏ:**
  ```powershell
  vagrant up --debug
  ```

### 2. Khi Ubuntu hoặc Kết nối SSH báo lỗi (Trên Control Node / Managed Node)

- **Lỗi Ansible báo `UNREACHABLE`:**
  Đứng từ máy Control Node, dùng lệnh ping mạng cơ bản để xem 2 máy có thông nhau không:
  ```bash
  ping 192.168.x.x
  ```

- **Lỗi `Permission denied` (Từ chối đăng nhập):**
  Lên máy Managed Node, kiểm tra xem Firewall có đang chặn cổng hay không:
  ```bash
  sudo ufw status
  ```
  *(Cần đảm bảo Port 22 / ALLOW / Anywhere).*

- **Xem lịch sử log lỗi của dịch vụ SSH:**
  Nếu SSH đang chạy nhưng vẫn không vào được, hãy đọc log bảo mật trên Managed Node:
  ```bash
  sudo tail -n 20 /var/log/auth.log
  ```

- **Lỗi xung đột "Vân tay" SSH (REMOTE HOST IDENTIFICATION HAS CHANGED):**
  Chạy lệnh sau trên Control Node để xóa lịch sử IP cũ (thay bằng IP thực tế bị lỗi):
  ```bash
  ssh-keygen -f ~/.ssh/known_hosts -R '192.168.x.x'
  ```