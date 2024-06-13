import os
import requests
import cv2
import time
import logging
from telegram import Bot
from datetime import datetime, timedelta

# Логирование в файл
logging.basicConfig(
    filename='monitoring.log',  # Имя файла для логов
    filemode='a',               # Режим добавления записей в файл (a - append, w - write)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Параметры RTSP
RTSP_URL = ["rtsp://your_rtsp_stream","rtsp://your_rtsp_stream2",...]
RTSP_CHECK_INTERVAL = 60        # Интервал проверки в секундах
FPS_THRESHOLD = 5               # Пороговое значение FPS

# Параметры для проверки наличия файлов
FOLDER_PATH = "your_folder_path"
FILE_CHECK_INTERVAL = 1800      # Интервал проверки в секундах (30 минут)

# Параметры Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Функция для отправки уведомлений в Telegram
def send_telegram_notification(bot: Bot, message: str):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Функция для мониторинга RTSP потока
def monitor_rtsp_stream(bot: Bot):
    while True:
        cap = cv2.VideoCapture(RTSP_URL)

        if not cap.isOpened():
            logger.error("Не удалось открыть RTSP поток")
            send_telegram_notification(bot, "Не удалось открыть RTSP поток")
            time.sleep(RTSP_CHECK_INTERVAL)
            continue

        frame_count = 0
        start_time = time.time()

        while time.time() - start_time < RTSP_CHECK_INTERVAL:
            ret, frame = cap.read()
            if not ret:
                logger.error("Ошибка при чтении кадра")
                send_telegram_notification(bot, "Ошибка при чтении кадра")
                break
            frame_count += 1

        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time

        logger.info(f"FPS: {fps:.2f}")
        if fps < FPS_THRESHOLD:
            message = f"Падение FPS ниже порогового значения: {fps:.2f}"
            logger.warning(message)
            send_telegram_notification(bot, message)

        cap.release()
        time.sleep(RTSP_CHECK_INTERVAL)

# Функция для мониторинга новых файлов в папке
def monitor_folder(bot: Bot):
    last_check_time = datetime.now()

    while True:
        now = datetime.now()
        new_files = [f for f in os.listdir(FOLDER_PATH)
                     if os.path.isfile(os.path.join(FOLDER_PATH, f))
                     and datetime.fromtimestamp(os.path.getmtime(os.path.join(FOLDER_PATH, f))) > last_check_time]

        if not new_files:
            logger.warning("Нет новых файлов в папке за последние 30 минут")
            send_telegram_notification(bot, "Нет новых файлов в папке за последние 30 минут")

        last_check_time = now
        time.sleep(FILE_CHECK_INTERVAL)
      
# Функция для пингования камеры
def ping_camera(bot: Bot):
    while True:
        try:
            response = requests.get(CAMERA_IP, timeout=10)
            if response.status_code == 200:
                logger.info("Камера доступна по IP: %s", CAMERA_IP)
            else:
                logger.warning("Камера вернула ошибку. Код состояния: %d", response.status_code)
                send_telegram_notification(bot, f"Камера вернула ошибку. Код состояния: {response.status_code}")
        except requests.RequestException as e:
            logger.error("Ошибка при подключении к камере: %s", e)
            send_telegram_notification(bot, f"Ошибка при подключении к камере: {e}")

        time.sleep(CHECK_INTERVAL)
        
if __name__ == '__main__':
    bot = Bot(token=TELEGRAM_TOKEN)

    # Запускаем мониторинг RTSP и проверки файлов в папке в отдельных потоках
    from threading import Thread
    rtsp_thread = Thread(target=monitor_rtsp_stream, args=(bot,))
    folder_thread = Thread(target=monitor_folder, args=(bot,))
    
    rtsp_thread.start()
    folder_thread.start()
    
    rtsp_thread.join()
    folder_thread.join()
