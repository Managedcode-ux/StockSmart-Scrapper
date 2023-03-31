# ROUTES GO HERE


from fastapi import APIRouter
from loguru import logger as log
import httpx
from time import time
import asyncio
from .services import scrape_stock


router = APIRouter()


stock_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
STOCK_CACHE = {}
CACHE_TIME = 60


@router.get("/scrape/stock/{symbol}")
async def stock_scrapper(symbol: str):
    data = await scrape_stock(symbol, stock_client, STOCK_CACHE, CACHE_TIME)
    return data


@router.on_event("startup")
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


@router.on_event("shutdown")
async def app_shutdown():
    await stock_client.__aexit__()
