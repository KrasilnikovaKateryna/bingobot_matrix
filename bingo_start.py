# Путь к первому скрипту
import subprocess

SCRIPT_PATH = "bingobot.py"

# Время в секундах (2 часа)
RESTART_INTERVAL = 2 * 60 * 60  # 7200 секунд

# Функция для запуска первого скрипта
def start_and_watch():
    while True:
        print("Запускаем первый скрипт...")
        process = subprocess.Popen(["python3", SCRIPT_PATH])

        try:
            # Ожидаем завершения процесса или таймаута в 2 часа
            process.wait(timeout=RESTART_INTERVAL)
            # Если процесс завершился до таймаута
            print(f"Скрипт завершился с кодом {process.returncode}. Перезапуск...")
        except subprocess.TimeoutExpired:
            # Таймаут достигнут: 2 часа прошли
            print("Прошло 2 часа. Перезапускаем скрипт...")
            process.terminate()  # Отправляем сигнал завершения
            try:
                # Ждём корректного завершения процесса
                process.wait(timeout=10)
                print("Скрипт завершён корректно.")
            except subprocess.TimeoutExpired:
                # Если процесс не завершился, принудительно убиваем его
                process.kill()
                print("Скрипт был принудительно завершён.")
            print("Перезапуск скрипта...")

if __name__ == "__main__":
    try:
        start_and_watch()
    except KeyboardInterrupt:
        print("Watchdog остановлен.")