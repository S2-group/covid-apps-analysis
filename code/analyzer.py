import json
from datetime import datetime
import os
import shutil
import re
import configuration as c

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

# Fill the Overview section of the report
def fill_overview(app, metadata, template, report_folder):
    
    icon_path = 'icon.png'
    c.download(metadata['icon'], report_folder + icon_path)

    screenshots = ''
    for i, s in enumerate(metadata['screenshots'], start=1):
        s_path = 'screenshot_' + str(i) + '.png'
        screenshots = screenshots + ' | <img src="<<<REBASE_ME>>>' + s_path + '" alt="screenshot" width="300"/> '
        if i % 3 == 0:
            screenshots = screenshots + ' | \n'  
        c.download(s, report_folder + s_path) 

    placeholders = {
        'ICON_PATH': '<<<REBASE_ME>>>' + icon_path,
        'SEPARATOR': c.SEPARATOR,
        'APP_TITLE': metadata['title'],
        'APP_VERSION': app['latest_crawled_version'],
        'APP_ID': app['id'],
        'APP_SUMMARY': metadata['summaryHTML'],
        'APP_PRIVACY_POLICY': metadata['privacyPolicy'],
        'APP_UPDATED': datetime.fromtimestamp(metadata['updated']),
        'APP_RECENT_CHANGES': metadata['recentChangesHTML'],
        'APP_INSTALLS': metadata['installs'],
        'APP_GENRE': metadata['genre'],
        'APP_RELEASE': metadata['released'],
        'APP_SIZE': metadata['size'],
        'APP_ANDROID_VERSION': metadata['androidVersionText'],
        'APP_DESCRIPTION': '> ' + re.sub('[\n|\r]+','\n<br>', metadata['description']),
        'SCREENSHOTS': screenshots
    }

    placeholders = fill_voids(placeholders)
    return fill_placeholders(placeholders, template)

# Given the portion of json file produced by Androwarm, it extracts a more structured and mapped data structure with placeholders 
def get_sdk_info(aw, sdk_info):
    
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

    # Iterate over all codenames and when they match we produce the filled string to be put in the report
    for e in sdk_info['codenames']:
        if e['api_level'] == target_sdk:
            result['target_sdk'] = e['codename'] + ', version ' + e['version'] + ' (API level ' + str(e['api_level']) + ')'
        if e['api_level'] == effective_sdk:
            result['effective_sdk'] = e['codename'] + ', version ' + e['version'] + ' (API level ' + str(e['api_level']) + ')'
        if e['api_level'] == min_sdk:
            result['min_sdk'] = e['codename'] + ', version ' + e['version'] + ' (API level ' + str(e['api_level']) + ')'
        if e['api_level'] == max_sdk:
            result['max_sdk'] = e['codename'] + ', version ' + e['version'] + ' (API level ' + str(e['api_level']) + ')'

    return result


# Fill the Android section of the report
def get_android_sdk(app, androwarn):

    sdk_info = json.load(open('static_resources/android_codenames.json', 'r'))

    mapped_info = get_sdk_info(androwarn[3]['androidmanifest.xml'][1][1], sdk_info)

    data = {
        'TARGET_SDK': mapped_info['target_sdk'],
        'EFFECTIVE_SDK': mapped_info['effective_sdk'],
        'MIN_SDK': mapped_info['min_sdk'],
        'MAX_SDK': mapped_info['max_sdk']
    }

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
def analyse_sdks(app, androwarn_data):

    print('Analyzing ' + app['id'])
    android_sdks = get_android_sdk(app, androwarn_data)
    print(android_sdks)

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
    for app in non_covid_apps:
        app['is_covid'] = False
    
    apps = covid_apps + non_covid_apps
    for app in apps:
        # We fetch all data from the json files
        metadata, reviews, servers, androguard, androwarn = load_data(app)
        analyse_sdks(app, androwarn)


def main():
    run_analysis("../")

if __name__ == "__main__":
    main()