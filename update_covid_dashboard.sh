#!/bin/bash

cd ~/covid_data/COVID-19/csse_covid_19_data/csse_covid_19_time_series
git pull
python3 ~/covid_data/covid-analysis/examine_covid_data.py /home/ec2-user/covid_data/COVID-19/csse_covid_19_data/ && aws s3 --recursive cp ~/covid_data/covid-analysis/html_graph_files/ s3://timheard-web-server/
