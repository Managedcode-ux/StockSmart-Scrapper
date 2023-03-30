# main.py
from fastapi import FastAPI
from loguru import logger as log
import httpx
from time import time
import asyncio
from parsel import Selector

# create API app object
app = FastAPI()
stock_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
STOCK_CACHE = {}
CACHE_TIME = 60
# attach route to our API app


async def scrape_yahoo_finance(symbol):

    cache = STOCK_CACHE.get(symbol)
    if cache and time()-CACHE_TIME < cache["_scrapped_on"]:
        log.debug(f"{symbol}: returning cached item")
        return cache

    log.info(f"{symbol}: scrapping data")

    response = await stock_client.get(
        f"https://finance.yahoo.com/quote/{symbol}?p={symbol}"
    )

    sel = Selector(response.text)
    parsed = {}

    rows = sel.xpath(
        '//div[re:test(@data-test,"(left|right)-summary-table")]//td[@data-test]')
    for row in rows:
        label = row.xpath("@data-test").get().split("-value")[0].lower()
        value = " ".join(row.xpath(".//text()").getall())
        parsed[label] = value

    parsed["price"] = (sel.css(
        f'fin-streamer[data-field="regularMarketPrice"][data-symbol="{symbol}"]::attr(value)'
    ).get())

    parsed["_scrapped_on"] = time()

    STOCK_CACHE[symbol] = parsed

    return parsed


@app.get("/scrape/stock/{symbol}")
async def scrape_stock(symbol: str):
    symbol = symbol.upper()
    return await scrape_yahoo_finance(symbol)


@app.on_event("startup")
async def app_startup():
    await stock_client.__aenter__()

    async def clear_expired_cache(period=60.0):
        while True:
            global STOCK_CACHE
            log.debug(f"Clearing expired cache")

            STOCK_CACHE = {
                k: v for k, v in STOCK_CACHE.items() if time()-CACHE_TIME < v["_scrapped_on"]
            }

            await asyncio.sleep(period)

    clear_cache_task = asyncio.create_task(clear_expired_cache())


@app.on_event("shutdown")
async def app_shutdown():
    await stock_client.__aexit__()


# print(httpx.get("http://127.0.0.1:8000/scrape/stock/aapl").json())
