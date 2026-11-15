#!/usr/bin/env bash

for arquivo in *.csv; do
    [ -e "$arquivo" ] || continue
    parquet="${arquivo%.csv}.parquet"
    duckdb -c "COPY (SELECT * FROM read_csv_auto('$arquivo')) TO '$parquet' (FORMAT PARQUET);"
done
