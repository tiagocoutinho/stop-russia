import asyncio
import random

import aiohttp
from async_timeout import timeout


def Target(url, pattern=None):
    return dict(url=url, pattern=pattern or url, nb_requests=0, nb_errors=0, message="", last="", total=0)

targets = [
    # https://lenta.ru/news/2022/02/28/obletim/
    Target('https://lenta.ru',  pattern='https://lenta.ru/news/{year:04}/{month:02}/{day:02}/{text}/'),
    # https://ria.ru/20220223/shoygu-1275575159.html
    Target('https://ria.ru/', pattern='https://ria.ru/{year:04}{month:02}{day:02}/{text}-{number}.html'),
    Target('https://ria.ru/lenta/'),
    # https://www.rbc.ru/politics/26/02/2022/6219ec289a79470d35420698
    Target('https://www.rbc.ru/', pattern='https://www.rbc.ru/politics/{day:02}/{month:02}/{year:04}/{text}'),
    Target('https://www.interfax.ru/', pattern='https://www.interfax.ru/search/?sw={text}'),
    Target('https://www.rt.com/'),
    Target('http://kremlin.ru/'),
    Target('http://en.kremlin.ru/'),
    Target('https://smotrim.ru/'),
    Target('https://tass.ru/'),
    Target('https://tvzvezda.ru/'),
    Target('https://vsoloviev.ru/'),
    Target('https://www.1tv.ru/'),
    Target('https://www.vesti.ru/'),
    Target('https://online.sberbank.ru/'),
    Target('https://sberbank.ru/'),
    Target('https://gosuslugi.ru/'),
    Target('https://mil.ru'),
    Target('https://iz.ru'),
    Target('https://yandex.ru/'),
    Target('https://sputniknews.com/'),
    Target('https://inosmi.ru/'),
    Target('https://gazeta.ru/'),
    Target('https://kommersant.ru/'),
    Target('https://rubaltic.ru/', pattern='https://www.rubaltic.ru/search/?q={text}'),
    Target('https://ura.news/'),
    Target('https://radiokp.ru/'),
    Target('https://echo.msk.ru/'),
    Target('https://life.ru/'),
]

def gen_url(target):
    return target['pattern'].format(
        year = random.randint(2010, 2022),
        month = random.randint(1, 12),
        day = random.randint(1, 30),
        number = random.randint(1_000_000_000, 9_000_000_000),
        text = "".join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789-', k=random.randint(3, 10)))
    )


async def get(session, target, max_time=None):
    target['last'] = url = gen_url(target)
    try:
        async with timeout(max_time) as timer:
            async with session.get(url) as response:
                if response.ok:
                    target['message'] = f"It was ok :-("
                else:
                    target['nb_errors'] += 1
                    target['message'] = f"http error: {response.status}"
                target['total'] += len(await response.text())
    except Exception as error:
        target['message'] = f"error: {error!r}"
    finally:
        target['nb_requests'] += 1
        print(target['url'], target['message'])



async def get_all(session, max_time=None):
    tasks = [asyncio.create_task(get(session, target, max_time)) for target in targets]
    await asyncio.wait(tasks)


async def main():

    async with aiohttp.ClientSession() as session:
        while True:
            print(40*"=")
            await get_all(session, 2)
        print(targets[0])


asyncio.run(main())

