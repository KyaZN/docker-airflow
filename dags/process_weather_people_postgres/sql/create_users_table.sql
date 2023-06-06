CREATE TABLE IF NOT EXISTS {{ params.table_name }} (
    user_id int,
    first_name varchar(200),
    last_name varchar(200),
    email varchar(150),
    gender varchar(10),
    age int,
    city varchar(200),
    lat_location varchar(200),
    lon_location varchar(200)
);