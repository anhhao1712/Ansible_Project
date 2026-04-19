-- Bang servers: danh sach cac node trong he thong
CREATE TABLE IF NOT EXISTS servers (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  hostname    VARCHAR(100) NOT NULL,
  ip          VARCHAR(50)  NOT NULL,
  role        VARCHAR(50)  DEFAULT 'web',
  status      VARCHAR(50)  DEFAULT 'running',
  deployed_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_hostname (hostname)
);

-- Bang deploy_logs: lich su deploy cua Ansible
CREATE TABLE IF NOT EXISTS deploy_logs (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  server     VARCHAR(100) NOT NULL,
  task       VARCHAR(255) NOT NULL,
  result     VARCHAR(50)  DEFAULT 'success',
  created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- Seed: danh sach server
INSERT INTO servers (hostname, ip, role, status) VALUES
  ('node1', '192.168.80.139', 'web', 'running'),
  ('node2', '192.168.80.140', 'db',  'running')
ON DUPLICATE KEY UPDATE status = 'running', deployed_at = NOW();

-- Seed: lich su deploy
INSERT INTO deploy_logs (server, task, result) VALUES
  ('node1', 'Docker Engine installed',    'success'),
  ('node1', 'WordPress container started','success'),
  ('node1', 'Nginx reverse proxy started','success'),
  ('node1', 'Firewall (UFW) configured',  'success'),
  ('node2', 'Docker Engine installed',    'success'),
  ('node2', 'MySQL container started',    'success'),
  ('node2', 'Seed data loaded',           'success'),
  ('node2', 'Firewall (UFW) configured',  'success');
