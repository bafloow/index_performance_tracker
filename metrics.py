from db import get_connection
import pandas as pd
import numpy as np


def get_index_data(index_name, period, con):
    with con.cursor() as cur:
        cur.execute(
            f"""
            WITH newest_dates AS (
            SELECT DISTINCT date
            FROM daily_prices
            ORDER BY date DESC
            LIMIT {period + 1}
            )
            SELECT 
            ci.symbol, s.name AS sector,
            ss.name AS sub_sector,
            dp.date, dp.close, dp.open, dp.volume,
            ic.weight_percentage AS weight
            FROM indexes ind
            JOIN index_components ic ON ic.index_id = ind.id
            JOIN company_info ci ON ci.id = ic.company_id
            LEFT JOIN sectors s ON s.id = ci.sector_id
            LEFT JOIN sub_sectors ss ON ss.id = ci.sub_sector_id
            JOIN daily_prices dp ON dp.company_id = ci.id
            JOIN newest_dates nd ON nd.date = dp.date
            WHERE ind.name = %s
            ORDER BY ci.symbol, dp.date
            """, (index_name,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        df = pd.DataFrame(data=rows,columns=cols)

        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = df['close'].astype(float)
            df['open'] = df['open'].astype(float)
            df['weight'] = df['weight'].astype(float) / 100

        return df
        
    

def get_daily_returns(df):
    df['daily_return'] = df.sort_values(by=['date'], ascending=True).groupby(['symbol'])['close'].pct_change()
    df.sort_values(['symbol','date']) 
    return df

def get_total_return(df_daily):

    df = df_daily.groupby('symbol').agg(
        symbol=('symbol','first'),
        sector=('sector','first'),
        sub_sector=('sub_sector', 'first'),
        weight=('weight', 'first'),
        start_price=('close', 'first'),
        end_price=('close', 'last'),
        daily_std=('daily_return', 'std')
    )

    df['total_return'] = (df['end_price'] - df['start_price'])/df['start_price']
    df['contribution'] = df['total_return'] * df['weight']
    df['volatility'] = df['daily_std'] * np.sqrt(252)

    return df

    

def get_sector_performance(df_week):
    
    df = df_week.groupby('sector').agg(
        weight=('weight','sum'),
        contribution=('contribution','sum')
    )

    return df

def get_sub_sector_performance(df_week):

    df = df_week.groupby('sub_sector').agg(
        weight=('weight','sum'),
        contribution=('contribution','sum')
    )

    return df
     



