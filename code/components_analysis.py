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
from scipy import stats
import numpy as np

def analyse_components(apps):
    #Set range of interest
    #activities: 2, services: 3, receivers: 4, providers: 5
    allComponents = slice(2,6)
    activities = slice(2,3)
    services = slice(3,4)
    receivers = slice(4,5)
    providers = slice(5,6)

    analyse_components_in_range(apps, allComponents)

def analyse_components_in_range(apps, components):
    #Calculate the number of modules for each app.
    for app in apps:
        app['componentNumber'] = sum(len(a[1]) for a in app['androwarn'][3]['androidmanifest.xml'][components])
        
    executeTTest(apps, components)
    generateChart(apps, components)

def executeTTest(apps, components):
    #t-test between covid and non-covid apps
    componentsC = []
    componentsNC = []
        
    for app in [a for a in apps if a['is_covid'] == True]:
        componentsC.append(sum(len(a[1]) for a in app['androwarn'][3]['androidmanifest.xml'][components]))

    for app in [a for a in apps if a['is_covid'] == False]:
        componentsNC.append(sum(len(a[1]) for a in app['androwarn'][3]['androidmanifest.xml'][components]))
    
    print("COVID APP DATA")
    print("Len: {}.".format(len(componentsC)))
    print("Mean: {}.".format(np.mean(componentsC)))
    print("Var: {}.".format(np.var(componentsC)))
    
    print("NON-COVID APP DATA")
    print("Len: {}.".format(len(componentsNC)))
    print("Mean: {}.".format(np.mean(componentsNC)))
    print("Var: {}.".format(np.var(componentsNC)))
    
    stat, p = stats.mannwhitneyu(componentsC,componentsNC)
    print("Mann-Whitney: U={}, n(c)={}, n(nc)={}, p-value={}.".format(stat, len(componentsC), len(componentsNC), p))
    
def generateChart(apps, components):
    df = pd.DataFrame(apps)
    
    # Align the colors to the other analyses
    color_1 = '#FFFFB3'
    color_2 = '#8DD2C7'
    colors_list = [color_1, color_2]
    sns.set_palette(sns.color_palette(colors_list))
    
    plot = sns.boxplot(data=df, x="is_covid", y="componentNumber")
    plot.set_xticklabels(['non-COVID', 'COVID'])
    plot.set(xlabel='', ylabel='Number of components')
    fig = plot.get_figure()
    fig.savefig(c.figures_path + 'componentNumber-receivers.pdf')
    sns.reset_defaults()