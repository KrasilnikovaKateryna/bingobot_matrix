import subprocess

# Путь к первому скрипту
SCRIPT_PATH = "bingobot.py"


# Функция для запуска первого скрипта
def start_and_watch():
    while True:
        print("Запускаем первый скрипт...")
        process = subprocess.Popen(["python3", SCRIPT_PATH])

        # Ожидаем завершения первого скрипта
        process.wait()

        # Логируем завершение
        print(f"Скрипт завершился с кодом {process.returncode}. Перезапуск...")


if __name__ == "__main__":
    try:
        start_and_watch()
    except KeyboardInterrupt:
        print("Watchdog остановлен.")