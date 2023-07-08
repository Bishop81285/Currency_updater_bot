import json
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.utils.request import Request

CURRENCY_RATES_FILE = "currency_rates.json"
load_dotenv()
API_KEY = os.environ['EXCHANGE_RATES_API_KEY']
BOT_TOKEN = os.environ['TG_BOT_API']
CHAT_ID = [os.environ['TG_CHAT_ID_1'], os.environ['TG_CHAT_ID_2']]
CHECK_INTERVAL = timedelta(minutes=30)

bot = Bot(token=BOT_TOKEN, request=Request())


def get_currency_rate(currency: str) -> float:
    """Получает курс валюты от API и возвращает его в виде float"""

    url = f"https://api.apilayer.com/exchangerates_data/latest?base={currency}"
    response = requests.get(url, headers={'apikey': API_KEY})
    response_data = json.loads(response.text)
    rate = response_data["rates"]["RUB"]

    return rate


def save_to_json(data: dict) -> None:
    """Сохраняет данные в JSON-файл"""

    with open(CURRENCY_RATES_FILE, "a") as f:
        if os.stat(CURRENCY_RATES_FILE).st_size == 0:
            json.dump([data], f)
        else:
            with open(CURRENCY_RATES_FILE) as json_file:
                data_list = json.load(json_file)
            data_list.append(data)
            with open(CURRENCY_RATES_FILE, "w") as json_file:
                json.dump(data_list, json_file)


def send_update_to_telegram(data: dict) -> None:
    """Отправляет обновление о курсе валюты в Telegram"""
    message = f"Курс {data['currency']} к рублю: {data['rate']:.2f}"
    for chat_id in CHAT_ID:
        bot.send_message(chat_id=chat_id, text=message)


def check_currency_rate() -> None:
    """
        Проверяет курс валюты и отправляет обновления в Telegram,
        если курс отличается от предыдущего сохраненного значения
        """
    while True:
        currency = input("Введите название валюты (USD или EUR): ").upper()

        if currency not in ("USD", "EUR"):
            print("Некорректный ввод")
            continue

        rate = get_currency_rate(currency)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"Курс {currency} к рублю: {rate:.2f}")
        data = {"currency": currency, "rate": rate, "timestamp": timestamp}

        previous_data = None

        with open(CURRENCY_RATES_FILE) as json_file:
            data_list = json.load(json_file)

            if data_list:
                previous_data = data_list[-1]

        if previous_data is None or data["rate"] != previous_data["rate"]:
            save_to_json(data)
            send_update_to_telegram(data)

        choice = input("Выберите действие: (1 - продолжить, 2 - выйти) ")

        if choice == "1":
            continue
        elif choice == "2":
            break
        else:
            print("Некорректный ввод")


def main():
    """
    Основная функция программы.
    Проверяет курс валюты и отправляет обновления в Telegram,
    если курс отличается от предыдущего сохраненного значения.
    """
    while True:
        check_currency_rate()
        next_check = datetime.now() + CHECK_INTERVAL
        print(f"Следующая проверка будет выполнена в {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
        while datetime.now() < next_check:
            pass


if __name__ == "__main__":
    main()
