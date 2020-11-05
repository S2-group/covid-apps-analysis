import json
from datetime import datetime
import os
import shutil
import re
import pandas as pd  
import seaborn as sns
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import configuration as c
from scipy.stats import wilcoxon

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
    fig.savefig(c.figures_path + 'min_sdk.pdf')

    # We reset the just-created figure so to do not have the subsequent plots on top of the old one
    plot_min_sdk.get_figure().clf()

    plot_target_sdk = sns.boxplot(data=df, x="is_covid", y="target_sdk", palette="Set3")
    plot_target_sdk.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plot_target_sdk.set(ylim=(0, 30))
    fig = plot_target_sdk.get_figure()
    fig.savefig(c.figures_path + 'target_sdk.pdf')

    # We reset the figure again
    plot_target_sdk.get_figure().clf()