from db import get_connection
import pandas as pd
import numpy as np


def calc_daily_gk(df_stock):

    log_hl = np.log(df_stock['high']/df_stock['low'])
    log_co = np.log(df_stock['close']/df_stock['open'])

    daily_gk = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1 ) * (log_co ** 2)
    
    return daily_gk


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
            dp.high, dp.low,
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
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)

        return df
        
    

def get_daily_returns(df):
    df['daily_return'] = df.sort_values(by=['date'], ascending=True).groupby(['symbol'])['close'].pct_change()
    df['daily_gk'] = calc_daily_gk(df)
    df = df.sort_values(['symbol','date']).reset_index(drop=True) 
    return df

def get_total_return(df_daily):

    df = df_daily.groupby('symbol').agg(
        symbol=('symbol','first'),
        sector=('sector','first'),
        sub_sector=('sub_sector', 'first'),
        weight=('weight', 'first'),
        start_price=('close', 'first'),
        end_price=('close', 'last'),
        var=('daily_return', 'var'),
        gk_var=('daily_gk','mean')
    )

    df['total_return'] = (df['end_price'] - df['start_price'])/df['start_price']
    df['contribution'] = df['total_return'] * df['weight']
    df['std_vol'] = np.sqrt(df['var'] * 252)
    df['gk_vol'] = np.sqrt(df['gk_var'] * 252)

    return df

    

def get_sector_performance(df_week, group='sector'):

   df_copy = df_week.copy()
   group_weight_sum = df_copy.groupby(group)['weight'].transform('sum')
   df_copy['intra_group_weight'] = df_copy['weight'] / group_weight_sum

   df_copy['weighted_var'] = df_copy['var'] * df_copy['intra_group_weight']
   df_copy['weighted_gk_var'] = df_copy['gk_var'] * df_copy['intra_group_weight']

   df = df_copy.groupby(group).agg(
        weight=('weight','sum'),
        contribution=('contribution','sum'),
        var=('weighted_var','sum'),
        gk_var=('weighted_gk_var','sum')
   )

   df['total_return'] = df['contribution'] / df['weight']
   df['std_vol'] = np.sqrt(df['var'] * 252)
   df['gk_vol'] = np.sqrt(df['gk_var'] * 252)
   
   return df



     



