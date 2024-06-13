import os
import requests
import cv2
import time
import logging
from telegram import Bot
from datetime import datetime
from threading import Thread

# Логирование в файл
logging.basicConfig(
    filename='monitoring.log',  # Имя файла для логов
    filemode='a',               # Режим добавления записей в файл (a - append, w - write)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Параметры RTSP
RTSP_URLs = ["rtsp://your_rtsp_stream", "rtsp://your_rtsp_stream2", "...", "rtsp://your_rtsp_stream20"]
RTSP_CHECK_INTERVAL = 60        # Интервал проверки в секундах
FPS_THRESHOLD = 5               # Пороговое значение FPS

# Параметры для проверки наличия файлов
FOLDER_PATHs = ["your_folder_path", "your_folder_path1", "...", "your_folder_path20"]
FILE_CHECK_INTERVAL = 2400      # Интервал проверки в секундах (40 минут)

# Параметры Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Функция для отправки уведомлений в Telegram
def send_telegram_notification(bot: Bot, message: str):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Функция для мониторинга RTSP потока
def monitor_rtsp_stream(bot: Bot, rtsp_url: str):
    while True:
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            logger.error(f"Не удалось открыть RTSP поток: {rtsp_url}")
            send_telegram_notification(bot, f"Не удалось открыть RTSP поток: {rtsp_url}")
            time.sleep(RTSP_CHECK_INTERVAL)
            continue

        frame_count = 0
        start_time = time.time()

        while time.time() - start_time < RTSP_CHECK_INTERVAL:
            ret, frame = cap.read()
            if not ret:
                logger.error(f"Ошибка при чтении кадра из потока: {rtsp_url}")
                send_telegram_notification(bot, f"Ошибка при чтении кадра из потока: {rtsp_url}")
                break
            frame_count += 1

        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time

        logger.info(f"FPS для {rtsp_url}: {fps:.2f}")
        if fps < FPS_THRESHOLD:
            message = f"Падение FPS ниже порогового значения для {rtsp_url}: {fps:.2f}"
            logger.warning(message)
            send_telegram_notification(bot, message)

        cap.release()
        time.sleep(RTSP_CHECK_INTERVAL)

# Функция для мониторинга новых файлов в папке
def monitor_folder(bot: Bot, folder_path: str):
    last_check_time = datetime.now()

    while True:
        now = datetime.now()
        new_files = [f for f in os.listdir(folder_path)
                     if os.path.isfile(os.path.join(folder_path, f))
                     and datetime.fromtimestamp(os.path.getmtime(os.path.join(folder_path, f))) > last_check_time]

        if not new_files:
            logger.warning(f"Нет новых файлов в папке {folder_path} за последние 40 минут")
            send_telegram_notification(bot, f"Нет новых файлов в папке {folder_path} за последние 40 минут")

        last_check_time = now
        time.sleep(FILE_CHECK_INTERVAL)

if __name__ == '__main__':
    bot = Bot(token=TELEGRAM_TOKEN)

    for i in range(len(RTSP_URLs)):
        RTSP_URL = RTSP_URLs[i]
        FOLDER_PATH = FOLDER_PATHs[i]

        # Запускаем мониторинг RTSP и проверки файлов в папке в отдельных потоках
        rtsp_thread = Thread(target=monitor_rtsp_stream, args=(bot, RTSP_URL))
        folder_thread = Thread(target=monitor_folder, args=(bot, FOLDER_PATH))
        
        rtsp_thread.start()
        folder_thread.start()
        
        rtsp_thread.join()
        folder_thread.join()
