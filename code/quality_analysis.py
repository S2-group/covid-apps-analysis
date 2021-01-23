import json
from datetime import datetime
import os
import shutil
import re
import pandas as pd  
import seaborn as sns
import csv
import scipy.stats
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import configuration as c

def csv_dict_list(file):
    reader = csv.DictReader(file)
    dict_list = []
    for line in reader:
        dict_list.append(line)
    return dict_list

def get_sq_results(app, sq_data):
    app_name = app['id'] + c.SEPARATOR + app['latest_crawled_version'] + '.apk'
    for sq_entry in sq_data:
        if(sq_entry['Name'] == app_name):
            return sq_entry

def make_numeric(item):
    if item == '-' or item == '':
        return None
    else:
        return float(item)

def polish_data(data):
    polished_data = {}
    polished_data['bugs'] = make_numeric(data['Bugs'])
    polished_data['vulnerabilities'] = make_numeric(data['Vulnerabilities'])
    polished_data['smells'] = make_numeric(data['Code Smells'])
    polished_data['duplication'] = make_numeric(data['Duplication'])
    polished_data['locs'] = make_numeric(data['#LOC'])
    return polished_data

def plot(df, var_name, label):
    to_plot = sns.boxplot(data=df, x='is_covid', y=var_name, palette="Set3", order=[True, False])
    to_plot.set_xticklabels(['COVID', 'non-COVID'])
    to_plot.set(xlabel='', ylabel=label)
    fig = to_plot.get_figure()
    fig.savefig(c.figures_path + var_name + '.png')
    to_plot.get_figure().clf()

    values_covid = df[df['is_covid'] == True][var_name].tolist()
    values_non_covid = df[df['is_covid'] == False][var_name].tolist()
    stats, p = scipy.stats.mannwhitneyu(values_covid, values_non_covid, alternative='two-sided')
    print('P-value for the Mann-Whitney stat on variable ' + var_name + ': ' + str(p))

# Analyze the SonarQube results 
def analyse_quality(apps):

    with open('../data/sonarqube_data.csv', newline='') as csv_file:
        sq_data = csv_dict_list(csv_file)
        for app in apps:
            sq_results = get_sq_results(app, sq_data)
            sq_results = polish_data(sq_results)
            app['bugs'] = sq_results['bugs']
            app['vulnerabilities'] = sq_results['vulnerabilities']
            app['smells'] = sq_results['smells']
            app['duplication'] = sq_results['duplication']
            app['locs'] = sq_results['locs']
    
    df = pd.DataFrame(apps) 
    print(df.describe())

    plot(df, 'bugs', 'Number of bugs')
    plot(df, 'vulnerabilities', 'Number of vulnerabilities')
    plot(df, 'smells', 'Number of code smells')
    plot(df, 'duplication', 'Level of code duplication')
    plot(df, 'locs', 'Number of lines of code')