import json
from datetime import datetime
import os
import shutil
import re
import pandas as pd  
import seaborn as sns
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
import configuration as c
import permission_analysis
import sdk_analysis
import components_analysis

# Loads all the json files one by one containing the data which will populate the report
def load_data(app):
    # We do not proceed if the 'latest_crawled_version' is not present, this happens when the app has never been crawled.
    if(not 'latest_crawled_version' in app):
        return None, None, None, None, None
    
    app_suffix_path = app['id'] + c.SEPARATOR + app['latest_crawled_version']

    metadata_path = c.DATA_PATH + app_suffix_path + c.SEPARATOR + 'metadata.json'
    metadata = json.load(open(metadata_path, 'r'))
    
    reviews_path = c.DATA_PATH + app_suffix_path + c.SEPARATOR + 'reviews.json'
    reviews = json.load(open(reviews_path, 'r'))

    servers_path = c.DATA_PATH + app_suffix_path + c.SEPARATOR + 'servers.json'
    if(os.path.exists(servers_path)):
        servers = json.load(open(servers_path, 'r'))
    else:
        servers = None

    androguard_path = c.DATA_PATH + app_suffix_path + c.SEPARATOR + 'androguard.json'
    if(os.path.exists(androguard_path)):
        androguard = json.load(open(androguard_path, 'r'))
    else:
        androguard = None

    androwarn_path = c.DATA_PATH + app_suffix_path + c.SEPARATOR + 'androwarn.json'
    if(os.path.exists(androguard_path)):
        androwarn = json.load(open(androwarn_path, 'r'))
    else:
        androwarn = None

    return metadata, reviews, servers, androguard, androwarn

# We run the full analysis on the apps
def run_analysis(input_path):
    
    # We don't even start if the provided path does not exist
    if os.path.exists(input_path):
        c.setPaths(input_path)
    else:
        print('Error - the provided path does not exist: ' + input_path)
        exit()

    all_apps = json.load(open(input_path + 'apps.json', 'r'))
    covid_apps = all_apps['covid_apps']
    non_covid_apps = all_apps['non_covid_apps']

    for app in covid_apps:
        app['is_covid'] = True
        app['corresponding_covid_app_id'] = None
    for app in non_covid_apps:
        app['is_covid'] = False
    
    apps = covid_apps + non_covid_apps
    for app in apps:
        # We fetch all data from the json files
        metadata, reviews, servers, androguard, androwarn = load_data(app)
        app['metadata'] = metadata
        app['reviews'] = reviews
        app['servers'] = servers
        app['androguard'] = androguard
        app['androwarn'] = androwarn
    
    sdk_analysis.analyse_sdks(apps)
    permission_analysis.analyse_permissions(apps)
    components_analysis.analyse_components(apps)

def main():
    run_analysis(c.root_path)

if __name__ == "__main__":
    main()