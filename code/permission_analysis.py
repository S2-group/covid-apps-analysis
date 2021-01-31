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
import numpy as np

all_apps_permissions_counts = []
permission_counts_covid_apps = []
permission_counts_non_covid_apps = []
permission_frequencies_covid = dict()
permission_frequencies_non_covid = dict()
permission_protection_levels = dict()
protection_level_app_frequencies_covid = dict()
protection_level_app_frequencies_non_covid = dict()
protection_level_app_permission_frequencies_covid = dict()
protection_level_app_permission_frequencies_non_covid = dict()

permissions_stats_file = open(c.figures_path + "permissions_stats.txt", "w")

def sort_dictionary(dictionary, key_or_value):
    return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[key_or_value])}

def count_permissions_per_app(app):
    global all_apps_permissions_counts
    global permission_counts_covid_apps
    global permission_counts_non_covid_apps
    all_apps_permissions_counts.append(app['permission_count'])
    if app['is_covid']:
        permission_counts_covid_apps.append(app['permission_count'])
    else:
        permission_counts_non_covid_apps.append(app['permission_count'])

def count_apps_per_permission(app):
    global permission_frequencies_covid
    global permission_frequencies_non_covid
    for permission in app['permissions']:
        permission_name = permission[permission.rindex('.')+1:]

        if app['is_covid']:
            if permission_name in permission_frequencies_covid.keys():
                permission_frequencies_covid[permission_name] += 1
            else:
                permission_frequencies_covid[permission_name] = 1
        else:
            if permission_name in permission_frequencies_non_covid.keys():
                permission_frequencies_non_covid[permission_name] += 1
            else:
                permission_frequencies_non_covid[permission_name] = 1

def compute_median_number_of_permissions(df):
    permissions_stats_file.write("Median # of permissions:\n" + str(df.groupby(['app_type'])['permission_count'].median()))
    permissions_stats_file.write("\n-------------------------------------\n")

def generate_boxplots_of_permission_counts_per_app(df):
    #### Boxplot of the number of permissions of COVID and Non-COVID apps ####
    boxplot_num_permissions = sns.boxplot(data=df, x="app_type", y="permission_count", palette="Set3")
    boxplot_num_permissions.yaxis.set_major_locator(ticker.MultipleLocator(1))
    boxplot_num_permissions.set(ylim=(0, max(all_apps_permissions_counts)), xlabel='Apps', ylabel='# of permissions')
    fig = boxplot_num_permissions.get_figure()
    fig.set_size_inches(6, 8)
    fig.savefig(c.figures_path + 'num_permissions.pdf')
    
    fig.clf()

def generate_separate_bar_charts_of_permission_fequencies(top):
    sorted_permission_frequencies_covid = sort_dictionary(permission_frequencies_covid, 1) 
    sorted_permission_frequencies_non_covid = sort_dictionary(permission_frequencies_non_covid, 1) 

    # COVID permissions
    plt.barh(range(top), list(sorted_permission_frequencies_covid.values())[-top:])
    plt.yticks(range(top), list(sorted_permission_frequencies_covid.keys())[-top:])
    plt.xlabel('Frequency (# of apps)')
    plt.ylabel('Permission')
    plt.gcf().set_size_inches(8, 5)
    plt.savefig(c.figures_path + 'permission_frequencies_covid.pdf', bbox_inches='tight')

    plt.clf()

    # Non-COVID permissions
    plt.barh(range(top), list(sorted_permission_frequencies_non_covid.values())[-top:])
    plt.yticks(range(top), list(sorted_permission_frequencies_non_covid.keys())[-top:])
    plt.xlabel('Frequency (# of apps)')
    plt.ylabel('Permission')
    plt.gcf().set_size_inches(8, 5)
    plt.savefig(c.figures_path + 'permission_frequencies_non_covid.pdf', bbox_inches='tight')

    plt.clf()

def generate_combined_bar_chart_of_permission_fequencies(top='all'):
    permission_frequencies_df = pd.DataFrame({'covid':pd.Series(permission_frequencies_covid),'non_covid':pd.Series(permission_frequencies_non_covid)}).fillna(0)

    permission_frequencies_df.covid = (permission_frequencies_df.covid / total_number_of_covid_apps * 100)
    permission_frequencies_df.non_covid = (permission_frequencies_df.non_covid / total_number_of_non_covid_apps * 100)

    permission_frequencies_df = permission_frequencies_df.sort_values('covid', ascending=True)
    displayed_permissions = permission_frequencies_df if top=='all' else permission_frequencies_df.tail(top)

    positions = list(range(len(displayed_permissions.index)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5 + len(displayed_permissions.index)/6))
    ax.barh([pos + width/2 for pos in positions], displayed_permissions['covid'], width, label='COVID', color=['#95cbc1'])
    ax.barh([pos - width/2 for pos in positions], displayed_permissions['non_covid'], width, label='Non-COVID', color=['#f6f6bd'])

    ax.set_xlabel('Frequency (% of apps)')
    ax.set_ylabel('Permission')
    ax.set_xticks(np.arange(0, 101, 10))
    ax.set_yticks(positions)
    ax.set_yticklabels(list(displayed_permissions.index))
    ax.legend()

    fig.savefig(c.figures_path + str(top) + '_permission_frequencies_percentages_covid_and_non_covid.pdf', bbox_inches='tight')

    fig.clf()

def identify_permissions_only_in_covid_or_non_covid():
    permissions_only_in_covid = permission_frequencies_covid.keys() - permission_frequencies_non_covid.keys()
    permissions_only_in_non_ovid = permission_frequencies_non_covid.keys() - permission_frequencies_covid.keys()
    
    permissions_stats_file.write("Permissions only in COVID:\n")
    for permission in permissions_only_in_covid:
        permissions_stats_file.write("\t" + permission + ": " + str(permission_frequencies_covid[permission]) + "\n")

    permissions_stats_file.write("\nPermissions only in Non-COVID:\n")
    for permission in permissions_only_in_non_ovid:
        permissions_stats_file.write("\t" + permission + ": " + str(permission_frequencies_non_covid[permission]) + "\n")
    
    permissions_stats_file.write("-------------------------------------\n")

def measure_difference_in_permission_frequencies():
    permissions_only_in_covid = permission_frequencies_covid.keys() - permission_frequencies_non_covid.keys()
    permissions_only_in_non_ovid = permission_frequencies_non_covid.keys() - permission_frequencies_covid.keys()

    # Add permissions that do not exist in the other category of apps with zero frequency
    all_permissions_covid = permission_frequencies_covid
    all_permissions_non_covid = permission_frequencies_non_covid
    for permission in permissions_only_in_covid:
        all_permissions_non_covid[permission] = 0
    for permission in permissions_only_in_non_ovid:
        all_permissions_covid[permission] = 0
    
    # Sort permissions based name
    all_permissions_covid = sort_dictionary(all_permissions_covid, 0)
    all_permissions_non_covid = sort_dictionary(all_permissions_non_covid, 0)
    
    # Run Wilcoxon signed-sum test
    wilcox = wilcoxon(list(all_permissions_covid.values()), list(all_permissions_non_covid.values()), correction=True)
    permissions_stats_file.write("Permission frequencies:\nwilcoxon signed-rank test p-value:" + str(wilcox.pvalue))
    permissions_stats_file.write("\n-------------------------------------\n")

def extract_protection_levels_of_permissions():
    all_unique_permissions = set(list(permission_frequencies_covid.keys()) + list(permission_frequencies_non_covid.keys()))
    
    android_permissions = json.load(open(c.STATIC_RESOURCES_PATH + 'android_permissions.json', 'r'))
    permission_details = android_permissions['permissions']

    for permission in permission_details:
        protection_level = permission_details[permission]['protection_level']
        protection_level = 'Not for third-party apps' if 'Not for use by third-party applications' in protection_level else protection_level # very long name to plot
        protection_level = 'signature | [others]' if 'signature|' in protection_level else protection_level # very long name to plot
        permission_protection_levels[permission] = protection_level

def get_app_protecition_levels(app_permissions):
    app_protecition_levels = []
    for permission in app_permissions:
        if permission in permission_protection_levels.keys():
            protection_level = permission_protection_levels[permission]
            protection_level = 'Not for third-party apps' if 'Not for use by third-party applications' in protection_level else protection_level # very long name to plot
            protection_level = 'signature | [others]' if 'signature|' in protection_level else protection_level # very long name to plot
        else:
            protection_level = 'undefined'

        app_protecition_levels.append(protection_level)
    return app_protecition_levels

def count_apps_per_protection_level(app):
    global protection_level_app_frequencies_covid
    global protection_level_app_frequencies_non_covid

    unique_protection_levels = set(list(permission_protection_levels.values()) + ['undefined'])

    for protection_level in unique_protection_levels:
        protection_level_count = app['protection_levels'].count(protection_level)
        
        if app['is_covid']:
            if protection_level in protection_level_app_permission_frequencies_covid:
                protection_level_app_permission_frequencies_covid[protection_level].append(protection_level_count)
            else:
                protection_level_app_permission_frequencies_covid[protection_level] = [protection_level_count]
        else:
            if protection_level in protection_level_app_permission_frequencies_non_covid:
                protection_level_app_permission_frequencies_non_covid[protection_level].append(protection_level_count)
            else:
                protection_level_app_permission_frequencies_non_covid[protection_level] = [protection_level_count]
        
        if protection_level in app['protection_levels']:
            if app['is_covid']:
                if protection_level in protection_level_app_frequencies_covid:
                    protection_level_app_frequencies_covid[protection_level] += 1
                else:
                    protection_level_app_frequencies_covid[protection_level] = 1
            else:
                if protection_level in protection_level_app_frequencies_non_covid:
                    protection_level_app_frequencies_non_covid[protection_level] += 1
                else:
                    protection_level_app_frequencies_non_covid[protection_level] = 1
        
def count_permissions_per_app_per_protection_level(app):
    global protection_level_app_frequencies_covid
    global protection_level_app_frequencies_non_covid

    unique_protection_levels = set(permission_protection_levels.values())

    for protection_level in unique_protection_levels:
        if protection_level in app['protection_levels']:
            if app['is_covid']:
                if protection_level in protection_level_app_frequencies_covid:
                    protection_level_app_frequencies_covid[protection_level] += 1
                else:
                    protection_level_app_frequencies_covid[protection_level] = 1
            else:
                if protection_level in protection_level_app_frequencies_non_covid:
                    protection_level_app_frequencies_non_covid[protection_level] += 1
                else:
                    protection_level_app_frequencies_non_covid[protection_level] = 1

    for protection_level in app['protection_levels']:
        
        #permission_name = permission[permission.rindex('.')+1:]
        if app['is_covid']:
            if protection_level in protection_level_app_permission_frequencies_covid.keys():
                protection_level_app_permission_frequencies_covid[protection_level] += 1
            else:
                protection_level_app_permission_frequencies_covid[protection_level] = 1
        else:
            if protection_level in protection_level_app_permission_frequencies_non_covid.keys():
                protection_level_app_permission_frequencies_non_covid[protection_level] += 1
            else:
                protection_level_app_permission_frequencies_non_covid[protection_level] = 1

def generate_combined_bar_chart_of_app_protection_levels():
    global total_number_of_covid_apps
    global total_number_of_non_covid_apps

    protection_level_frequencies_df = pd.DataFrame({'covid':pd.Series(protection_level_app_frequencies_covid),'non_covid':pd.Series(protection_level_app_frequencies_non_covid)}).fillna(0)
    protection_level_frequencies_df = protection_level_frequencies_df.sort_values('covid', ascending=True)

    protection_level_frequencies_df.covid = (protection_level_frequencies_df.covid / total_number_of_covid_apps * 100)
    protection_level_frequencies_df.non_covid = (protection_level_frequencies_df.non_covid / total_number_of_non_covid_apps * 100)

    positions = list(range(len(protection_level_frequencies_df.index)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5 + len(protection_level_frequencies_df.index)/6))
    ax.barh([pos + width/2 for pos in positions], protection_level_frequencies_df['covid'], width, label='COVID', color=['#95cbc1'])
    ax.barh([pos - width/2 for pos in positions], protection_level_frequencies_df['non_covid'], width, label='Non-COVID', color=['#f6f6bd'])

    ax.set_xlabel('Frequency (% of apps)')
    ax.set_ylabel('Protection level')
    ax.set_xticks(np.arange(0, 101, 10))
    ax.set_yticks(positions)
    ax.set_yticklabels(list(protection_level_frequencies_df.index))
    ax.legend()

    fig.savefig(c.figures_path + 'protection_levels_app_frequencies_percentages_covid_and_non_covid.pdf', bbox_inches='tight')

    fig.clf()

def generate_boxplots_of_protection_level_counts_per_app():
    protection_levels_df_covid = pd.DataFrame([(key, var) for (key, L) in protection_level_app_permission_frequencies_covid.items() for var in L], columns=['protection_level', 'number_of_permissions'])
    protection_levels_df_covid['app_type'] = 'COVID'
    protection_levels_df_non_covid = pd.DataFrame([(key, var) for (key, L) in protection_level_app_permission_frequencies_non_covid.items() for var in L], columns=['protection_level', 'number_of_permissions'])
    protection_levels_df_non_covid['app_type'] = 'Non-COVID'
    protection_levels_df_all = pd.concat([protection_levels_df_covid, protection_levels_df_non_covid])

    unique_protection_levels = set(list(permission_protection_levels.values()) + ['undefined'])

    only_these_protection_levels = []
    for protection_level in unique_protection_levels:
        if sum(protection_level_app_permission_frequencies_covid[protection_level]) > 0 or sum(protection_level_app_permission_frequencies_non_covid[protection_level]) > 0:
            only_these_protection_levels.append(protection_level)
    
    # Added this order manually to make the plot looks better 
    only_these_protection_levels = ['normal', 'dangerous', 'undefined', 'signature', 'signature | [others]', 'Deprecated', 'Not for third-party apps']
    
    boxplot_num_protection_levels = sns.boxplot(data=protection_levels_df_all, y="protection_level", x="number_of_permissions", hue="app_type", palette="Set3", orient = 'h', order=only_these_protection_levels)
    boxplot_num_protection_levels.set(xlim=(-1, 25), xlabel='# of permissions per app', ylabel='Protection levels')
    plt.legend(loc='lower right')
    #boxplot_num_protection_levels.set_xticklabels(boxplot_num_protection_levels.get_xticklabels(), rotation=90) # for vertical boxplots
    boxplot_num_protection_levels.legend_.set_title(None)
    fig = boxplot_num_protection_levels.get_figure()
    fig.set_size_inches(8, 5)
    fig.savefig(c.figures_path + 'num_protection_levels.pdf', bbox_inches='tight')
    fig.clf()

# Analyze app permissions
def analyse_permissions(apps):
    global total_number_of_covid_apps
    global total_number_of_non_covid_apps
    total_number_of_covid_apps = 0
    total_number_of_non_covid_apps = 0

    for app in apps:
        app['app_type'] = 'COVID' if app['is_covid'] else 'Non-COVID'
        app['permissions'] = app['androguard']['permissions']
        app['permission_count'] = len(app['permissions'])

        if app['is_covid']:
            total_number_of_covid_apps += 1
        else:
            total_number_of_non_covid_apps += 1

        count_permissions_per_app(app)

        count_apps_per_permission(app)

        extract_protection_levels_of_permissions()
        
        app['protection_levels'] = get_app_protecition_levels(app['permissions'])

        count_apps_per_protection_level(app)
    
    df = pd.DataFrame(apps)

    compute_median_number_of_permissions(df)

    generate_boxplots_of_permission_counts_per_app(df)
    
    generate_separate_bar_charts_of_permission_fequencies(top = 10) 

    generate_combined_bar_chart_of_permission_fequencies(top = 10)
    generate_combined_bar_chart_of_permission_fequencies() # all permissions

    identify_permissions_only_in_covid_or_non_covid()

    measure_difference_in_permission_frequencies()

    generate_combined_bar_chart_of_app_protection_levels()

    generate_boxplots_of_protection_level_counts_per_app()

    permissions_stats_file.close()