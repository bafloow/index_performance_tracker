from curl_cffi import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError
import pandas as pd

#url example url = 'https://query1.finance.yahoo.com/v8/finance/chart/NVDA?range=1y&interval=1d&events=history'

class Quote(BaseModel):
    close: list[float | None]
    low: list[float | None]
    volume: list[int | None]
    high: list[float | None]
    open: list[float | None]

class AdjClose(BaseModel):
    adjclose: list[float | None]

class Indicators(BaseModel):
    quote: list[Quote]
    adjclose: list[AdjClose]

class Result(BaseModel):
    timestamp: list[int]
    indicators: Indicators

class Chart(BaseModel):
    result: list[Result]

class YahooResponse(BaseModel):
    chart: Chart


def get_historical_price_data(url):

    res = requests.get(url, impersonate='safari184')
    res_json = res.json()

    try:
        validated_data = YahooResponse.model_validate(res_json)
        print('Response structure is correct')
    except ValidationError as e:
        print(f'Validation error: {e}')
        exit()

    chart_data = validated_data.chart.result[0]
    timestamp_data = chart_data.timestamp
    quote_data = chart_data.indicators.quote[0]

    df = pd.DataFrame(
        {
            'date': pd.to_datetime(timestamp_data, unit="s").date,
            'close': quote_data.close,
            'low': quote_data.low,
            'volume': quote_data.volume,
            'high': quote_data.high,
            'open': quote_data.open
        }
    )
    
    




