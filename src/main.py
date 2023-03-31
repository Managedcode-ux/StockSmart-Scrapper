# main.py
from fastapi import FastAPI
from Scrapping_Service.router import router as stock_scrapper

# create API app object
app = FastAPI()


app.include_router(stock_scrapper)
