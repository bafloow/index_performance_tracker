from price_history_scraper import get_historical_price_data
from datetime import datetime, timedelta, time
from db import get_connection

def modify_url(symbol, start_day = None, end_day = None):
    yahoo_symbol = symbol.replace('.','-')
    if symbol.startswith("^"):
        symbol = '%5E' + symbol[1:]

    if start_day is None:
        return f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=1y&interval=1d&events=history'

    if end_day is None:
        end_day = datetime.today().date() - timedelta(days=1)

    end_ts = int((datetime.combine(end_day, time(15,30))).timestamp())

    start_day = start_day + timedelta(days=1)
    start_ts = int((datetime.combine(start_day, time(15,30))).timestamp())
    return f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?period1={start_ts}&period2={end_ts}&interval=1d&events=history'


def insert_prices(url, id, con, table_name ='daily_prices', id_col = 'company_id'):
    df = get_historical_price_data(url)
    if df.empty:
        return

    df[id_col] = id
    price_tuples = [tuple(x) for x in df.to_numpy()]
            
    cols = ','.join(list(df.columns))
    values = ', '.join(['%s'] * len(df.columns))

    with con.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO {table_name}({cols})
            VALUES ({values})
            ON CONFLICT ({id_col}, date) DO UPDATE
            SET close = EXCLUDED.close,
                low = EXCLUDED.low,
                volume = EXCLUDED.volume,
                high = EXCLUDED.high,
                open = EXCLUDED.open
            """,
            (price_tuples)
            )
    con.commit()

    
def sync_prices(query, con, table_name, id_col):
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)

    with con.cursor() as cur:
        cur.execute(query)
        unique_dates = cur.fetchall()

    for symbol, id, max_date  in unique_dates:
        if max_date is None:
            ready_url = modify_url(symbol)
            
        elif max_date < yesterday:
            ready_url = modify_url(symbol, max_date, yesterday)
        
        else:
            continue

        insert_prices(url=ready_url, id=id, con=con, table_name=table_name, id_col=id_col)

def sync_all_prices():
    company_query = """
                    SELECT c.symbol, c.id, MAX(p.date) 
                    FROM company_info c
                    LEFT JOIN daily_prices p
                    ON c.id = p.company_id
                    GROUP BY c.symbol, c.id 
                    """
    index_query = """
                    SELECT i.id, i.symbol, MAX(ip.date)
                    FROM indexes i
                    LEFT JOIN index_prices ip
                    ON i.id = ip.index_id
                    GROUP BY i.symbol, i.id
                    """
    con = get_connection()
    try:
        sync_prices(query=company_query, con=con, table_name='daily_prices', id_col='company_id')
        sync_prices(query=index_query, con=con, table_name='index_prices', id_col='index_id')
    finally:
        con.close()

if __name__ == '__main__':
    sync_all_prices()
