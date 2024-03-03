# ds_db
Helper library to save results from deepstream application to database.
Also used by GUI application to query the database and visualize the analysis.

## Installation
Needs a postgres-database, this repo contains a docker-compose file to get it up and running
- Clone the repo git clone (path to repo)
- cd to ds_db folder and run "docker compose up"
- pip install -e . to install the library
- pip install pytest and then pytest . to run all unit-tests to verify the library is working
