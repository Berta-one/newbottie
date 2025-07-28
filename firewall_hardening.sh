
#!/bin/bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 8501
ufw enable
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
