# BUSINNESS LOGIC GOES HERE


from fastapi import APIRouter
from loguru import logger as log
import httpx
from time import time
import asyncio
from parsel import Selector


# attach route to our API app


async def scrape_yahoo_finance(symbol, stock_client, STOCK_CACHE, CACHE_TIME):
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


async def scrape_stock(symbol: str, stock_client: str, STOCK_CACHE: dict, CACHE_TIME: int):
    symbol = symbol.upper()
    return await scrape_yahoo_finance(symbol, stock_client, STOCK_CACHE, CACHE_TIME)
