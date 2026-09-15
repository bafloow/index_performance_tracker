from price_history_scraper import get_historical_price_data
from datetime import datetime
from db import get_connection

def modify_url(symbol):
    return f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d&events=history'

today = datetime.today().date()
con = get_connection()
cur = con.cursor()

cur.execute("SELECT symbol, id FROM company_info")

unique_companies = sorted(cur.fetchall())

for company in unique_companies:
    cur.execute("SELECT close FROM daily_prices WHERE company_id = %s AND date = %s ",(company[1],today,))
    res = cur.fetchone()
    if res is  None:
        ready_url = modify_url(company[0])
        df = get_historical_price_data(ready_url)
        df['company_id'] = company[1]

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

    else:
        continue

