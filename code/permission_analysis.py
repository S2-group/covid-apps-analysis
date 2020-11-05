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

# Analyze the permissions required by the app 
def analyse_permissions(apps):
    permissions_stats_file = open(c.figures_path + "permissions_stats.txt", "w")
    all_apps_permissions_counts = []
    permissions_counts_covid_apps = []
    permissions_counts_non_covid_apps = []
    permissions_frequencies_covid = dict()
    permissions_frequencies_non_covid = dict()

    ############ Pre-processing ############
    for app in apps:
        app['app_type'] = 'COVID' if app['is_covid'] else 'Non-COVID'
        app['permissions'] = app['androguard']['permissions']
        app['permission_count'] = len(app['permissions'])

        #### Count the number of permissions of each app ####
        all_apps_permissions_counts.append(app['permission_count'])
        if app['is_covid']:
            permissions_counts_covid_apps.append(app['permission_count'])
        else:
            permissions_counts_non_covid_apps.append(app['permission_count'])
        
        #### Count the number of apps that require each permission ####
        for permission in app['permissions']:
            permission_name = permission[permission.rindex('.')+1:]

            if app['is_covid']:
                if permission_name in permissions_frequencies_covid.keys():
                    permissions_frequencies_covid[permission_name] += 1
                else:
                    permissions_frequencies_covid[permission_name] = 1
            else:
                if permission_name in permissions_frequencies_non_covid.keys():
                    permissions_frequencies_non_covid[permission_name] += 1
                else:
                    permissions_frequencies_non_covid[permission_name] = 1

    df = pd.DataFrame(apps) 

    ############ Stats and Plots ############
    # Get the median number of permissions of COVID and Non-COVID apps
    permissions_stats_file.write("Median # of permissions:\n" + str(df.groupby(['app_type'])['permission_count'].median()))
    permissions_stats_file.write("\n-------------------------------------\n")

    #### Boxplot of the number of permissions of COVID and Non-COVID apps ####
    plot_num_permissions = sns.boxplot(data=df, x="app_type", y="permission_count", palette="Set3")
    plot_num_permissions.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plot_num_permissions.set(ylim=(0, max(all_apps_permissions_counts)), xlabel='Apps', ylabel='# of permissions')
    fig = plot_num_permissions.get_figure()
    fig.set_size_inches(6, 8)
    fig.savefig(c.figures_path + 'num_permissions.pdf')


    #### Clear figure ####
    plot_num_permissions.get_figure().clf()


    ##### Bar plot of permission frequencies of COVID and Non-COVID apps ####
    # Sort permissions based on frequency
    permissions_frequencies_covid = {k: v for k, v in sorted(permissions_frequencies_covid.items(), key=lambda item: item[1])}
    permissions_frequencies_non_covid = {k: v for k, v in sorted(permissions_frequencies_non_covid.items(), key=lambda item: item[1])}

    # COVID permissions
    top = 10 # Top 10 permissions --> to plot all permissions, we use: top = len(permissions_frequencies_covid)
    plt.barh(range(top), list(permissions_frequencies_covid.values())[-top:])
    plt.yticks(range(top), list(permissions_frequencies_covid.keys())[-top:])
    plt.xlabel('Frequency')
    plt.ylabel('Permission')
    fig.set_size_inches(8, 5)
    fig.savefig(c.figures_path + 'permissions_frequencies_covid.pdf', bbox_inches='tight')

    # Clear figure
    plot_num_permissions.get_figure().clf()

    # Non-COVID permissions
    top = 10
    plt.barh(range(top), list(permissions_frequencies_non_covid.values())[-top:])
    plt.yticks(range(top), list(permissions_frequencies_non_covid.keys())[-top:])
    plt.xlabel('Frequency')
    plt.ylabel('Permission')
    fig.set_size_inches(8, 5)
    fig.savefig(c.figures_path + 'permissions_frequencies_non_covid.pdf', bbox_inches='tight')


    #### Difference in permissions between COVID and Non-COVID ####
    permissions_only_in_covid = permissions_frequencies_covid.keys() - permissions_frequencies_non_covid.keys()
    permissions_only_in_non_ovid = permissions_frequencies_non_covid.keys() - permissions_frequencies_covid.keys()
    
    permissions_stats_file.write("Permissions only in COVID:\n")
    for permission in permissions_only_in_covid:
        permissions_stats_file.write("\t" + permission + ": " + str(permissions_frequencies_covid[permission]) + "\n")

    permissions_stats_file.write("\nPermissions only in Non-COVID:\n")
    for permission in permissions_only_in_non_ovid:
        permissions_stats_file.write("\t" + permission + ": " + str(permissions_frequencies_non_covid[permission]) + "\n")
    
    permissions_stats_file.write("-------------------------------------\n")


    #### Compute Wilcoxon signed-sum test to measure the difference in frequencies of permission in COVID and Non-COVID ####
    # Add permissions that do not exist in the other category of apps with zero frequency
    for permission in permissions_only_in_covid:
        permissions_frequencies_non_covid[permission] = 0
    for permission in permissions_only_in_non_ovid:
        permissions_frequencies_covid[permission] = 0
    
    # Sort permissions based name
    permissions_frequencies_covid = {k: v for k, v in sorted(permissions_frequencies_covid.items(), key=lambda item: item[0])}
    permissions_frequencies_non_covid = {k: v for k, v in sorted(permissions_frequencies_non_covid.items(), key=lambda item: item[0])}
    
    # Run Wilcoxon signed-sum test
    wilcox = wilcoxon(list(permissions_frequencies_covid.values()), list(permissions_frequencies_non_covid.values()), correction=True)
    permissions_stats_file.write("Permission frequencies:\nwilcoxon signed-rank test p-value:" + str(wilcox.pvalue))
    permissions_stats_file.write("\n-------------------------------------\n")

    permissions_stats_file.close()