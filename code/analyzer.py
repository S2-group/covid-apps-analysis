import json
from datetime import datetime
import os
import shutil
import re
import pandas as pd  
import seaborn as sns
import matplotlib.ticker as ticker
import configuration as c

figures_path = '../figures/'
root_path = '../'

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

# Given the portion of json file produced by Androwarm, it extracts a more structured and mapped data structure with placeholders 
def get_sdk_info(aw):
    
    result = {
        'target_sdk': None,
        'effective_sdk': None,
        'min_sdk': None,
        'max_sdk': None,
    }

    # We flatten the list into a string so to ease the application of the regexes below
    contents = '\n'.join(aw)

    target_sdk = re.findall(r'Declared target SDK:\s*(\d+)', contents) or None
    effective_sdk = re.findall(r'Effective target SDK:\s*(\d+)', contents) or None
    min_sdk = re.findall(r'Min SDK:\s*(\d+)', contents) or None
    max_sdk = re.findall(r'Max SDK:\s*(\d+)', contents) or None

    # Transform API levels into integers (when possible) so to ease the comparison in the subsequent for iteration 
    if not target_sdk is None:
        target_sdk = int(target_sdk[0])
    if not effective_sdk is None:
        effective_sdk = int(effective_sdk[0])
    if not min_sdk is None:
        min_sdk = int(min_sdk[0])
    if not max_sdk is None:
        max_sdk = int(max_sdk[0])
    
    result['target_sdk'] = target_sdk
    result['effective_sdk'] = effective_sdk
    result['min_sdk'] = min_sdk
    result['max_sdk'] = max_sdk

    return result


# Fill the Android section of the report
def get_android_sdk(app, androwarn):

    mapped_info = get_sdk_info(androwarn[3]['androidmanifest.xml'][1][1])
    data = {
        'target_sdk': mapped_info['target_sdk'],
        'min_sdk': mapped_info['min_sdk'],
        'max_sdk': mapped_info['max_sdk']
    }

    # In some cases the target_sdk is None, we will use the effective_sdk field in those cases
    if(data['target_sdk'] is None):
        data['target_sdk'] = mapped_info['effective_sdk']
    return data

# Retrieves the latest "amount" reviews of "stars" stars from "reviews"
def get_reviews(stars, amount, reviews):
    result = ''
    count = 0
    i = 0
    while count != amount and i < len(reviews):
        if reviews[i]['score'] == stars:
            count = count + 1
            result = result + '> ' + reviews[i]['content'].replace('**', '\*\*') + '<br> :date: __' + reviews[i]['at'] + '__\n\n'
        i = i + 1
    if count == 0:
        result = 'No recent reviews available with ' + str(stars) + ' stars.'
    return result

# Analyze the SDK levels defined in the Manifest of the app 
def analyse_sdks(apps):

    for app in apps:
        # print('Analyzing ' + app['id'])
        android_sdks = get_android_sdk(app, app['androwarn'])
        app['target_sdk'] = android_sdks['target_sdk']
        app['min_sdk'] = android_sdks['min_sdk']
        app['max_sdk'] = android_sdks['max_sdk']

    df = pd.DataFrame(apps) 

    plot_min_sdk = sns.boxplot(data=df, x="is_covid", y="min_sdk", palette="Set3")
    plot_min_sdk.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plot_min_sdk.set(ylim=(0, 30))
    fig = plot_min_sdk.get_figure()
    fig.savefig(figures_path + 'min_sdk.pdf')

    # We reset the just-created figure so to do not have the subsequent plots on top of the old one
    plot_min_sdk.get_figure().clf()

    plot_target_sdk = sns.boxplot(data=df, x="is_covid", y="target_sdk", palette="Set3")
    plot_target_sdk.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plot_target_sdk.set(ylim=(0, 30))
    fig = plot_target_sdk.get_figure()
    fig.savefig(figures_path + 'target_sdk.pdf')


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
    
    analyse_sdks(apps)


def main():
    run_analysis(root_path)

if __name__ == "__main__":
    main()