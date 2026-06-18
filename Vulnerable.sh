sudo systemctl stop fail2ban
sudo systemctl stop suricata
sudo ufw disable


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
