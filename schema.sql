
CREATE TABLE sectors (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE sub_sectors (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sector_id INT,
    name VARCHAR(255) NOT NULL UNIQUE,
    FOREIGN KEY(sector_id)
    REFERENCES sectors(id)
);

CREATE TABLE indexes (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE company_info (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255),
    sector_id INT,
    sub_sector_id INT,
    FOREIGN KEY(sector_id) 
    REFERENCES sectors(id),
    FOREIGN KEY(sub_sector_id)
    REFERENCES sub_sectors(id) 
);

CREATE TABLE index_components (
    company_id INT,
    index_id INT,
    weight_percentage DEC(5,2),
    FOREIGN KEY(company_id) 
    REFERENCES company_info(id) ON DELETE CASCADE,
    FOREIGN KEY(index_id)
    REFERENCES indexes(id) ON DELETE CASCADE,
    PRIMARY KEY(company_id, index_id)
);

CREATE TABLE daily_prices (
    company_id INT NOT NULL,
    date DATE NOT NULL,
    close DEC(12,4) NOT NULL,
    low DEC(12,4) NOT NULL,
    volume BIGINT NOT NULL,
    high DEC(12,4) NOT NULL,
    open DEC(12,4) NOT NULL,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) 
	REFERENCES company_info(id) ON DELETE CASCADE
);


