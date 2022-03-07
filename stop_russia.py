import time
import random
import asyncio

from aiohttp import ClientSession, ClientTimeout
from rich.live import Live
from rich.table import Table


def Target(url, pattern=None):
    return dict(
        url=url,
        base_url=url.removeprefix("http://").removeprefix("https://"),
        pattern=pattern or url,
        nb_requests=0,
        nb_errors=0,
        message="",
        last_url="",
        total=0,
        time=0,
    )


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

def format_data_size(size, decimals=2, binary_system=False):
    if binary_system:
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]
        largest_unit = "YiB"
        step = 1024
    else:
        units = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB"]
        largest_unit = "YB"
        step = 1000
    for unit in units:
        if size < step:
            break
        size /= step
    else:
        unit = largest_unit
    return f"{{:.{decimals}f}} {unit}".format(size)


def format_time(microsecs, decimals=2):
    units = [("µs", 1000), ("ms", 1000), ("s", 60), ("m", 0)]
    t = microsecs
    for unit, step in units:
        if t < step:
            break
        t /= step
    else:
        unit = "h"
    return f"{{:.{decimals}f}} {unit}".format(t)


def gen_url(target):
    return target['pattern'].format(
        year = random.randint(2010, 2022),
        month = random.randint(1, 12),
        day = random.randint(1, 30),
        number = random.randint(1_000_000_000, 9_000_000_000),
        text = "".join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789-', k=random.randint(3, 10)))
    )


async def get(session, target):
    start = time.monotonic()
    target['last_url'] = url = gen_url(target)
    try:
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
        target['time'] = time.monotonic() - start
    return target['time']


async def get_loop(session, target, max_freq=2):
    period = 1 / max_freq
    while True:
        dt = await get(session, target)
        if (nap := period - dt) > 0:
            await asyncio.sleep(nap)


async def get_loop_all(session):
    tasks = [asyncio.create_task(get_loop(session, target)) for target in targets]
    await asyncio.wait(tasks)


def table():
    table = Table("URL", "Reqs", "Errors", "Size", "Time", "Last", title="stats", min_width=120)
    for target in targets:
        style = "red" if ":-(" in target['message'] else None
        table.add_row(
            target['base_url'],
            str(target['nb_requests']),
            str(target['nb_errors']),
            format_data_size(target['total']),
            format_time(target['time']*1E6),
            target['message'][:40], style=style
        )
    return table


async def monitor():
    with Live(table(), auto_refresh=False) as live:
        while True:
            await asyncio.sleep(0.5)
            live.update(table(), refresh=True)


async def main():
    timeout = ClientTimeout(total=2)
    async with ClientSession(timeout=timeout) as session:
        fetcher = asyncio.create_task(get_loop_all(session))
        try:
            await monitor()
        except KeyboardInterrupt:
            print("Ctrl-C pressed. Bailing out")
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())

