#!/bin/bash
sudo rm -f /var/lib/fail2ban/fail2ban.sqlite3
sudo truncate -s 0 /var/log/fail2ban.log

sudo ufw enable
sudo systemctl start fail2ban
sudo systemctl start suricata

sudo fail2ban-client set sshd unbanip 192.168.137.1

echo "==================="
echo "   State of ufw   "
echo "==================="

sudo ufw status 

echo "======================="
echo "   State of fail2ban   "
echo "======================="

sudo systemctl status fail2ban

echo "========================"
echo "   State of suricata    "
echo "========================"
sudo systemctl status suricata
