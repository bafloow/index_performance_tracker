from ticker_scraper import get_sp500_data, get_nasdaq100_data
from db import get_connection
from time import sleep

wiki_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
wiki_nasdaq100 = 'https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies'
slick_sp500 = 'https://www.slickcharts.com/sp500'
slick_nasdaq100 = 'https://www.slickcharts.com/nasdaq100'


def sync_index_to_db(con, index_name, companies):
        with con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO indexes(name)
                VALUES (%s)
                ON CONFLICT(name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
                """,
                (index_name,)
            )
            index_id = cur.fetchone()[0]

            unique_sectors = sorted({company.sector for company in companies })

            sub_to_sector = {
                company.sub_industry: company.sector
                for company in companies
                if company.sub_industry and company.sector
            }

            cur.executemany(
                    """
                    INSERT INTO sectors(name)
                    VALUES (%s)
                    ON CONFLICT(name) DO NOTHING;
                    """,
                    [(sector,) for sector in unique_sectors]
            )

            cur.execute("SELECT name, id FROM sectors;")
            sector_map = dict(cur.fetchall())

            sub_sector_tuples = [
                (sub_name, sector_map[sec_name])
                for sub_name, sec_name in sub_to_sector.items()
                if sec_name in sector_map
            ]

            cur.executemany(
                """
                INSERT INTO sub_sectors(name, sector_id)
                VALUES (%s, %s)
                ON CONFLICT(name) DO NOTHING;
                """, 
                sub_sector_tuples
            )

            cur.execute("SELECT name, id FROM sub_sectors;")
            sub_sector_map = dict(cur.fetchall())

            company_tuples = [ (
                company.symbol,
                company.name,
                sector_map.get(company.sector),
                sub_sector_map.get(company.sub_industry),
            )
            for company in companies   
            ]

            cur.executemany(
                """
                INSERT INTO company_info(symbol, company_name, sector_id, sub_sector_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE
                SET company_name = EXCLUDED.company_name,
                    sector_id = EXCLUDED.sector_id,
                    sub_sector_id = EXCLUDED.sub_sector_id
                """,
                company_tuples,
            )

            cur.execute("SELECT symbol, id FROM company_info")
            company_map = dict(cur.fetchall())
            
            index_comp_tuples = [ (
                company_map.get(company.symbol),
                index_id,
                company.weight
            )
            for company in companies 
            ]

            cur.executemany(
                """
                INSERT INTO index_components(company_id, index_id, weight_percentage)
                VALUES (%s, %s, %s)
                ON CONFLICT (company_id, index_id) DO UPDATE
                SET weight_percentage = EXCLUDED.weight_percentage
                """,
                index_comp_tuples,
            )

            con.commit()
   
def sync_all_indexes():

    sp500_data = get_sp500_data(wiki_sp500, slick_sp500)
    nasdaq100_data = get_nasdaq100_data(wiki_nasdaq100, slick_nasdaq100, sp500_data)
    datasets = {
        "S&P500": sp500_data,
        "Nasdaq100": nasdaq100_data
        }

    con = get_connection()
    try:
        for name, data in datasets.items():
            sync_index_to_db(con, name, data)
            sleep(1)
    finally:
         con.close()

if __name__ == '__main__':
     sync_all_indexes()

    




        









  






