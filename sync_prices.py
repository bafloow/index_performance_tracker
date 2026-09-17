from price_history_scraper import get_historical_price_data
from datetime import datetime, timedelta, time
from db import get_connection

def modify_url(symbol, start_day = None, end_day = None):
    yahoo_symbol = symbol.replace('.','-')
    if start_day is None:
        return f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=1y&interval=1d&events=history'

    if end_day is None:
        end_day = datetime.today().date() - timedelta(days=1)

    end_ts = int((datetime.combine(end_day, time(15,30))).timestamp())

    start_day = start_day + timedelta(days=1)
    start_ts = int((datetime.combine(start_day, time(15,30))).timestamp())
    return f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?period1={start_ts}&period2={end_ts}&interval=1d&events=history'


def insert_prices(url, company_id, con, cur):
    df = get_historical_price_data(url)
    df['company_id'] = company_id
    
    price_tuples = [tuple(x) for x in df.to_numpy()]
            
    cols = ','.join(list(df.columns))
    values = ', '.join(['%s'] * len(df.columns))
    
    cur.executemany(
        f"""
        INSERT INTO daily_prices({cols})
        VALUES ({values})
        ON CONFLICT (company_id, date) DO UPDATE
        SET close = EXCLUDED.close,
            low = EXCLUDED.low,
            volume = EXCLUDED.volume,
            high = EXCLUDED.high,
            open = EXCLUDED.open
        """,
        (price_tuples)
        )
    con.commit()

    
today = datetime.today().date()
yesterday = today - timedelta(days=1)
con = get_connection()
cur = con.cursor()


cur.execute("SELECT symbol, id FROM company_info")
unique_companies = sorted(cur.fetchall())

for company in unique_companies:
    company_id = company[1]
    company_symbol = company[0]
    cur.execute("SELECT MAX(date) FROM daily_prices WHERE company_id = %s",(company_id,))
    res = cur.fetchone()

    if res[0] is None:
        ready_url = modify_url(company_symbol)
        insert_prices(ready_url, company_id, con, cur)
        
        

    elif res[0] < yesterday:
        ready_url = modify_url(company_symbol, res[0], yesterday)
        insert_prices(ready_url, company_id, con, cur)
        

    else:
        continue




