# 🧪 Testing Guide — Ansible IAC Project

---

# Bước 1 — Cài Dependencies

```bash
ansible-galaxy collection install -r requirements.yml
```

---

# Bước 2 — Mã hóa Secrets với Ansible Vault

## 2.1 — Tạo file secrets

```bash
cat > vault/secrets.yml << EOF
db_root_password: "root123"
db_name: "ansible_db"
db_user: "ansible_user"
db_password: "password123"
EOF
```

---

## 2.2 — Xem file trước khi mã hóa

```bash
cat vault/secrets.yml
```

---

## 2.3 — Mã hóa file

```bash
ansible-vault encrypt vault/secrets.yml
```

Password:
```text
vagrant
```

---

## 2.4 — Kiểm tra sau mã hóa

```bash
cat vault/secrets.yml
```

---

## 2.5 — Lưu vault password

```bash
echo "vagrant" > vault/.vault_pass
chmod 600 vault/.vault_pass
```

---

# Bước 3 — Deploy hệ thống

```bash
ansible-playbook playbooks/site.yml
```

---

# Bước 4 — Test Tags & Dry-run

```bash
ansible-playbook playbooks/site.yml --tags webapp --check
```

---

# Bước 5 — Test Backup

```bash
ansible-playbook playbooks/backup.yml
```

## Kiểm tra backup Web

```bash
ssh vagrant@192.168.80.139 "sudo ls -la /opt/backups/webapp/"
```

## Kiểm tra backup Database

```bash
ssh vagrant@192.168.80.140 "sudo ls -la /opt/backups/mysql/"
```

---

# Bước 6 — Test Health Check & Rollback

## 6.1 — Tắt Flask Container

```bash
ssh vagrant@192.168.80.139 "sudo docker stop flask_app"
```

---

## 6.2 — Health Check

```bash
ansible-playbook playbooks/healthcheck.yml
```

---

## 6.3 — Rollback

```bash
ansible-playbook playbooks/rollback.yml
```

---

## 6.4 — Kiểm tra lại

```bash
ansible-playbook playbooks/healthcheck.yml
```
