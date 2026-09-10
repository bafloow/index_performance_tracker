from curl_cffi import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional

class Company_Info(BaseModel):
    symbol: str
    name: str
    sector: str
    sub_industry : str
    weight : Optional[float] =None


wiki_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
wiki_nasdaq100 = 'https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies'
slick_sp500 = 'https://www.slickcharts.com/sp500'
slick_nasdaq100 = 'https://www.slickcharts.com/nasdaq100'

ICB_to_GICS = {
    "Technology": "Information Technology",
    "Telecommunications": "Communication Services",
    "Health Care": "Health Care",
    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Industrials": "Industrials",
    "Utilities": "Utilities",
    "Basic Materials": "Materials",
    "Energy": "Energy",
    "Financials": "Financials",
}

NON_SP500_GICS_OVERRIDE = {
    "ASML": ("Information Technology", "Semiconductors"),
    "AZN":  ("Health Care", "Pharmaceuticals"),
    "MELI": ("Consumer Discretionary", "Broadline Retail"),
    "PDD":  ("Consumer Discretionary", "Broadline Retail"),
    "ARM":  ("Information Technology", "Semiconductors"),
    "SNPS": ("Information Technology", "Application Software"),
    "TEAM": ("Information Technology", "Application Software"),
    "CRWD": ("Information Technology", "Systems Software"),
    "DASH": ("Consumer Discretionary", "Restaurants"),
}

def get_slick_weights(slick):

    res_slick = requests.get(slick, impersonate='safari184')
    soup_slick = BeautifulSoup(res_slick.content, 'html.parser')
    
    table_slick = soup_slick.find('table', attrs={'class':'table table-hover table-borderless table-sm'})
    rows_slick = table_slick.find_all('tr')
    
    weights = {}
    for row in rows_slick:
        cells = row.find_all('td')
    
        if not cells:
            continue
    
        symbol = cells[2].text.strip()
        weight = float(cells[3].text.strip().replace('%',''))
    
        weights[symbol] = weight
    
    return(weights)

def get_sp500_data(wiki, slick):

    weights = get_slick_weights(slick)

    res_wiki = requests.get(wiki, impersonate='safari184')
    soup_wiki = BeautifulSoup(res_wiki.content, 'html.parser')

    table_wiki = soup_wiki.find('table', id='constituents')

    tbody_wiki = table_wiki.find('tbody')
    rows_wiki = tbody_wiki.find_all('tr')

    companies = []
    for row in rows_wiki:
        cells = row.find_all('td')

        if not cells:
            continue

        symbol = cells[0].text.strip()
        name = cells[1].text.strip()
        sector = cells[2].text.strip()
        sub_industry = cells[3].text.strip()

        company = Company_Info(
            symbol=symbol,
            name=name,
            sector=sector,
            sub_industry=sub_industry,
            weight=weights.get(symbol)
        )
        companies.append(company)


    return(companies)


def get_nasdaq100_data(wiki,slick,sp500_companies):

    sp500_dict = {c.symbol : c for c in sp500_companies}

    weights = get_slick_weights(slick)

    res_wiki = requests.get(wiki, impersonate='safari184')
    soup_wiki = BeautifulSoup(res_wiki.content, 'html.parser')
    wiki_table = soup_wiki.find('table', id='constituents')

    tbody_wiki = wiki_table.find('tbody')
    rows_wiki = tbody_wiki.find_all('tr')

    nas_companies = []
    for row in rows_wiki:
        cells = row.find_all('td')

        if not cells:
            continue

        symbol = cells[0].text.strip()
        name = cells[1].text.strip()
        icb_sector = cells[2].text.strip()
        icb_sub_industry = cells[3].text.strip()

        if symbol in sp500_dict:
            sector = sp500_dict[symbol].sector
            sub_industry = sp500_dict[symbol].sub_industry
            name = sp500_dict[symbol].name
        elif symbol in NON_SP500_GICS_OVERRIDE:
            sector, sub_industry = NON_SP500_GICS_OVERRIDE[symbol]
        else:
            sector = ICB_to_GICS.get(icb_sector)
            sub_industry = icb_sub_industry

        company = Company_Info(
            symbol=symbol,
            name=name,
            sector=sector,
            sub_industry=sub_industry,
            weight=weights.get(symbol)
        )

        nas_companies.append(company)

    return(nas_companies)










        


        



    
    




        
           
    
    





    
    







