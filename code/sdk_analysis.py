import json
from datetime import datetime
import os
import shutil
import re
import pandas as pd  
import seaborn as sns
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
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

    # Align the colors to the other analyses
    color_1 = '#FFFFB3'
    color_2 = '#8DD2C7'
    colors_list = [color_1, color_2]
    sns.set_palette(sns.color_palette(colors_list))

    plot_min_sdk = sns.boxplot(data=df, x="is_covid", y="min_sdk")
    plot_min_sdk.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plot_min_sdk.set(ylim=(0, 30))
    plot_min_sdk.set_xticklabels(['non-COVID', 'COVID'])
    plot_min_sdk.set(xlabel='', ylabel='Minimum Android SDK version')
    plot_min_sdk.axhline(1, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,1-0.5, "1", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(5, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,5-0.5, "2", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(11, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,11-0.5, "3", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(14, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,14-0.5, "4", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(21, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,21-0.5, "5", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(23, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,23-0.5, "6", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(25, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,25-0.5, "7", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(27, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,27-0.5, "8", backgroundcolor='white', fontsize=8, horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(28, ls='--', linewidth=1, zorder=100, color='grey')
    # plot_min_sdk.text(0.5,28-0.5, "9", fontsize=8, horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.axhline(29, ls='--', linewidth=1, color='grey')
    plot_min_sdk.text(0.5,29-0.5, "10", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    # plot_min_sdk.axhline(30, ls='--', linewidth=1)
    # plot_min_sdk.text(0.5,30-0.5, "11", fontsize=8, horizontalalignment='center', verticalalignment='bottom')
    plot_min_sdk.annotate('Android versions', xy=(0.5, 6),  xycoords='data', xytext=(-55, 18), textcoords='offset points', size=12, ha='right', va="center", arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=80,rad=20"))
    fig = plot_min_sdk.get_figure()
    fig.savefig(c.figures_path + 'min_sdk.png')

    # We reset again the figure
    plot_min_sdk.get_figure().clf()

    plot_target_sdk = sns.boxplot(data=df, x="is_covid", y="target_sdk")
    plot_target_sdk.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plot_target_sdk.set(ylim=(0, 30))
    plot_target_sdk.set_xticklabels(['non-COVID', 'COVID'])
    plot_target_sdk.set(xlabel='', ylabel='Target Android SDK version')
    plot_target_sdk.axhline(1, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,1-0.5, "1", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(5, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,5-0.5, "2", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(11, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,11-0.5, "3", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(14, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,14-0.5, "4", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(21, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,21-0.5, "5", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(23, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,23-0.5, "6", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(25, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,25-0.5, "7", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(27, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,27-0.5, "8", backgroundcolor='white', fontsize=8, horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(28, ls='--', linewidth=1, zorder=100, color='grey')
    # plot_target_sdk.text(0.5,28-0.5, "9", fontsize=8, horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.axhline(29, ls='--', linewidth=1, color='grey')
    plot_target_sdk.text(0.5,29-0.5, "10", fontsize=8, backgroundcolor='white', horizontalalignment='center', verticalalignment='bottom')
    # plot_target_sdk.axhline(30, ls='--', linewidth=1)
    # plot_target_sdk.text(0.5,30-0.5, "11", fontsize=8, horizontalalignment='center', verticalalignment='bottom')
    plot_target_sdk.annotate('Android versions', xy=(0.5, 6),  xycoords='data', xytext=(-55, 18), textcoords='offset points', size=12, ha='right', va="center", arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=80,rad=20"))
    fig = plot_target_sdk.get_figure()
    fig.savefig(c.figures_path + 'target_sdk.png')

    # We reset the figure again
    sns.reset_defaults()
    plot_target_sdk.get_figure().clf()