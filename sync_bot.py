import requests
import time
from bs4 import BeautifulSoup
from lab4.constants import MY_URL
from typing import Any, Dict
from bs4.element import Tag


def check_token() -> None:
    """
    Функция для проверки токена.
    Вызывает метод getMe с помощью библиотеки requests.
    """
    url = f"{MY_URL}/getMe"
    print(requests.get(url))


def send_message(chat_id: int, text: str) -> None:
    """
    Функция для отправки сообщения пользователю.

    Args:
        chat_id - id пользователя
        text - текст, который нужно отправить

    Returns:
        Отправляет POST-запрос к методу sendMessage
    """
    url = f"{MY_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}

    requests.post(url, data)


def get_updates(offset: Any = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Функция для получения обновлений

    Args:
        offset - указатель на сообщение, с которого нужно отдавать обновления
        timeout - время, в течении которого ждут ответа

    Returns:
        Bозвращает JSON-объект со списком обновлений бота
    """
    url = f"{MY_URL}/getUpdates"

    parameters = {"offset": offset, "timeout": timeout}
    response = requests.get(url, params=parameters)
    data: dict[str, Any] = response.json()
    return data


def get_daily_quote() -> str:
    """
    Функция для получения цитаты.

    Returns:
        Bозвращает цитату с сайта
    """
    url = "https://quotes.toscrape.com/"
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    quote_block = soup.find("div", class_="quote")

    if not isinstance(quote_block, Tag):
        raise ValueError("Цитата не найдена")

    text_tag = quote_block.find("span", class_="text")
    if not isinstance(text_tag, Tag):
        raise ValueError("Цитата не найдена")

    author_tag = quote_block.find("small", class_="author")
    if not isinstance(author_tag, Tag):
        raise ValueError("Автор не найден")

    text = text_tag.text
    author = author_tag.text

    return f"Цитата:\n{text}\n {author}"


def main() -> None:
    """Oсновной цикл работы бота"""
    offset = None
    print("Запуск бота ^^")

    while True:
        updates = get_updates(offset)

        if "result" not in updates:
            time.sleep(1)
            continue

        for update in updates["result"]:
            update_id = update["update_id"]
            offset = update_id + 1

            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text")

            if not text:
                continue

            elif text == "/quote":
                quote = get_daily_quote()
                send_message(chat_id, quote)
            else:
                print("Получено сообщение:", text)
                send_message(chat_id, text)
