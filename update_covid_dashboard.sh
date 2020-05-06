#!/bin/bash

function create_covid_dashboard() {
    echo """
<!DOCTYPE html>
<meta http-equiv="Cache-control" content="No-Cache">
<html>
  <style>
    h1 {
        text-align: center;
    }

    h2 {
        text-align: center;
    }

    h3 {
        text-align: center;
    }

    div {
        text-align: center;
    }
  </style>
  
  <title>COVID-19 Heatmap</title>
  
  <body>
    <hr>
    <h1>Global</h1>
    <hr>
    <div>
      <iframe id="confirmed_global" width="30%" height="300px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_confirmed_global.html">
      </iframe>

      <iframe id="deaths_global" width="30%" height="300px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_deaths_global.html">
      </iframe>

      <iframe id="recovered_global" width="30%" height="300px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_recovered_global.html">
      </iframe>
    </div>

    <div>
      <iframe id="confirmed_global_line" width="30%" height="300px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_confirmed_global_line.html">
      </iframe>

      <iframe id="deaths_global_line" width="30%" height="300px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_deaths_global_line.html">
      </iframe>

      <iframe id="recovered_global_line" width="30%" height="300px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_recovered_global_line.html">
      </iframe>
    </div>

    <br>
    <br>
    <hr>
    <h1>United States</h1>
    <hr>

    <div>
      <iframe id="confirmed_us" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_confirmed_us.html">
      </iframe>
      
      <iframe id="deaths_us" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_deaths_us.html">
      </iframe>
    </div>

    <div>
      <iframe id="confirmed_us_line" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_confirmed_us_line.html">
      </iframe>
      
      <iframe id="deaths_us_line" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_deaths_us_line.html">
      </iframe>
    </div>
    
    <div>
      <iframe id="confirmed_us_counties" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_confirmed_us_counties.html">
      </iframe>
      
      <iframe id="deaths_us_counties" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_deaths_us_counties.html">
      </iframe>
    </div>

    <div>
      <iframe id="confirmed_us_counties_line" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_confirmed_us_counties_top_10_line.html">
      </iframe>
      
      <iframe id="deaths_us_counties_line" width="45%" height="500px" src="https://timheard-web-server.s3.eu-central-1.amazonaws.com/covid_deaths_us_counties_top_10_line.html">
      </iframe>
    </div>
    
    <br>
    <hr>
    <div>
    <b>Last Updated: $(date)</b>
    </div>
  </body>
</html>
""" > /home/ec2-user/covid_data/covid-analysis/html_graph_files/covid_dashboard.html
}

cd /home/ec2-user/covid_data/COVID-19/csse_covid_19_data/csse_covid_19_time_series
git pull
python3 /home/ec2-user/covid_data/covid-analysis/examine_covid_data.py /home/ec2-user/covid_data/COVID-19/csse_covid_19_data/
create_covid_dashboard
aws s3 --recursive cp /home/ec2-user/covid_data/covid-analysis/html_graph_files/ s3://timheard-web-server/


