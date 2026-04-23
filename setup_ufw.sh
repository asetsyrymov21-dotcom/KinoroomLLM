#!/usr/bin/env bash
# =============================================================
#  setup_ufw.sh — Настройка файервола UFW для VPS
#  Запуск: sudo bash setup_ufw.sh
#  Замените YOUR_HOME_IP на ваш реальный IP (узнать: curl ifconfig.me)
# =============================================================

YOUR_HOME_IP="YOUR_HOME_IP_HERE"   # ← ЗАМЕНИТЕ ПЕРЕД ЗАПУСКОМ

if [[ $EUID -ne 0 ]]; then
  echo "Запускайте от root: sudo bash $0"
  exit 1
fi

if [[ "$YOUR_HOME_IP" == "YOUR_HOME_IP_HERE" ]]; then
  echo "ОШИБКА: Укажите ваш IP в переменной YOUR_HOME_IP"
  echo "  Ваш текущий IP: $(curl -s ifconfig.me 2>/dev/null || echo 'не определён')"
  exit 1
fi

echo "[+] Сбрасываем правила UFW..."
ufw --force reset

echo "[+] Политика по умолчанию — блокировать всё входящее..."
ufw default deny incoming
ufw default allow outgoing

echo "[+] SSH — только с вашего IP (защита от брутфорса)..."
ufw allow from "$YOUR_HOME_IP" to any port 22 proto tcp

# Если нужен SSH с любого IP (менее безопасно):
# ufw allow 22/tcp

echo "[+] HTTP и HTTPS — открыты для всего интернета..."
ufw allow 80/tcp
ufw allow 443/tcp

echo "[+] Ваше приложение (порт 8001 Kinoroom nginx) — при необходимости..."
# Если 8001 нужен публично:
# ufw allow 8001/tcp
# Если только с вашего IP:
ufw allow from "$YOUR_HOME_IP" to any port 8001 proto tcp

echo "[+] Явно запрещаем порты БД с любых внешних адресов..."
ufw deny 5432/tcp
ufw deny 5433/tcp
ufw deny 3306/tcp   # MySQL (на случай если порт ещё открыт)

echo "[+] Защита от DDoS — ограничение соединений на SSH..."
ufw limit ssh/tcp

echo "[+] Включаем UFW..."
ufw --force enable

echo ""
echo "=== Текущие правила ==="
ufw status verbose

echo ""
echo "[+] Готово! Проверьте что SSH-соединение не разорвано."
echo "    Откройте новый терминал и убедитесь что можете подключиться."
