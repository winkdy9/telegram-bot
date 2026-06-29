import asyncio
from bs4 import BeautifulSoup
from lab4.constants import MY_URL, KEY_WEATHER
from lab4.sync_bot import get_daily_quote
from aiohttp import ClientSession
from typing import Any
from http import HTTPStatus


user_states: dict[int, str] = {}  # глобальный словарь


async def get_updates(session: ClientSession,
                      offset: int | None = None,
                      timeout: int = 30) -> dict[str, Any]:
    """
    Асинхронная функция для получения обновлений

    Args:
        session - объект для управления HTTP-соединениями,
                чтобы бот быстро и правильно делал запросы
        offset - указатель на сообщение, с которого нужно отдавать обновления
        timeout - время, в течении которого ждут ответа

    Returns:
        Bозвращает await JSON-объект со списком обновлений бота
    """
    url = f"{MY_URL}/getUpdates"

    if offset is not None:
        parameters = {"offset": offset, "timeout": timeout}
    else:
        parameters = {"timeout": timeout}
    async with session.get(url, params=parameters) as response:
        data: dict[str, Any] = await response.json()
        return data


async def send_message(session: ClientSession,
                       chat_id: int,
                       text: str) -> None:
    """
    Асинхронная функция для отправки сообщения пользователю.

    Args:
        session - объект для управления HTTP-соединениями,
                чтобы бот быстро и правильно делал запросы
        chat_id - id пользователя
        text - текст, который нужно отправить

    Returns:
        Отправляет POST-запрос к методу sendMessage
    """
    url = f"{MY_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}

    async with session.post(url, json=data):
        pass


async def quote(session: ClientSession) -> str:
    """
    Асинхронная функция для получения цитат.

    Args:
        session - объект для управления HTTP-соединениями,
                чтобы бот быстро и правильно делал запросы

    Returns:
        Bозвращает цитаты с сайта
    """
    url = "https://quotes.toscrape.com/"
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    quotes = soup.find_all("span", class_="text")[:3]
    return "\n" + "~~~Цитаты~~~\n" + "\n".join(q.text for q in quotes)


async def animal_news(session: ClientSession) -> str:
    """
    Асинхронная функция для получения новостей про животных.

    Args:
        session - объект для управления HTTP-соединениями,
                чтобы бот быстро и правильно делал запросы

    Returns:
        Bозвращает заголовки с сайта
    """
    url = "https://www.livescience.com/animals"
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    articles = soup.select("h2")[1:4]

    return "~~~Новости про животных~~~\n" + "\n".join(
        article.text.strip() for article in articles
    )


async def habr_news(session: ClientSession) -> str:
    """
    Асинхронная функция для получения новостей.

    Args:
        session - объект для управления HTTP-соединениями,
                чтобы бот быстро и правильно делал запросы

    Returns:
        Bозвращает заголовки с сайта
    """
    url = "https://habr.com/ru/all/"

    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("a.tm-title__link")[:3]

    return "\n"+"~~~Новости Habr~~~\n" + "\n".join(
        article.text.strip() for article in articles
    )


async def get_weather(session: ClientSession,
                      city: str) -> str:
    """
    Асинхронная функция для получения погоды из города city.

    Args:
        session - объект для управления HTTP-соединениями,
                чтобы бот быстро и правильно делал запросы
        city - город пользователя

    Returns:
        Bозвращает данные о погоде
    """
    url = "http://api.openweathermap.org/data/2.5/weather"

    if KEY_WEATHER is None:
        return "Ошибка нахождения ключа"
    params: dict[str, str] = {
        'q': city,
        'appid': KEY_WEATHER,
        'units': 'metric',
    }

    async with session.get(url=url, params=params) as response:
        status = response.status

        if status == HTTPStatus.OK:
            data = await response.json()
            return (
                f"Погода в {city}:\n"
                f"Температура: {data['main']['temp']}°C\n"
                f"Описание: {data['weather'][0]['description']}"
            )

        if status == HTTPStatus.NOT_FOUND:
            return "Город не найден:("

        return (
            "Произошла неизвестная ошибка при получении погоды. "
            "Попробуйте позже."
        )


async def main() -> None:
    """Oсновной цикл работы асинхронного бота"""
    offset = None
    print("Запуск асинхронного бота ^^")

    async with ClientSession() as session:
        while True:

            updates = await get_updates(session, offset)

            for update in updates.get("result", []):
                update_id = update["update_id"]
                offset = update_id + 1

                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text")

                if not text:
                    continue

                elif chat_id in user_states:
                    if user_states[chat_id] == 'waiting_for_city':
                        city = text
                        weather = await get_weather(session, city)
                        await send_message(session, chat_id, weather)

                        del user_states[chat_id]
                        continue

                elif text == "/headlines":
                    results = await asyncio.gather(
                        animal_news(session),
                        quote(session),
                        habr_news(session)
                    )
                    message = "\n".join(results)
                    await send_message(session, chat_id, message)

                elif text == "/quote":
                    quote1 = await asyncio.to_thread(get_daily_quote)
                    await send_message(session, chat_id, quote1)

                elif text == "/weather":
                    await send_message(session,
                                       chat_id,
                                       "Пожалуйста, введите название города.")
                    user_states[chat_id] = 'waiting_for_city'
                else:
                    print("Получено сообщение:", text)
                    await send_message(session, chat_id, text)


if __name__ == "__main__":
    asyncio.run(main())
