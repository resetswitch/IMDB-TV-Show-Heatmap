from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import os
import sys
import time
from datetime import datetime
import random


def windowsSafeFilename(filename):
    '''
    Converts the string to a windows friendly format, omitting
    any and all reserved character names

    Parameters
    ----------
    filename : string
        filename string (not including path)
        
    Returns
    -------
    Windows friendly filename string    
    '''

    reserved_characters = ["<",">",":","\"","/","\\","|","?", "*"]
    for rs in reserved_characters:
        filename = filename.replace(rs, "")
    
    return filename.replace('–','-')

def requestContent(URL):
    try:
        request_1 = requests.get(URL)
        request_1.raise_for_status()
    except requests.exceptions.RequestException as e:
        sys.exit("Most Likely you are being Denied for too many Connections at once, please try another TV Show or change to a VPN")
    return request_1.content

def safeFilenameFormat(string):       
    '''(string <string>)
    Takes in a string <string> (not including path) and converts the string to a windows friendly format, omitting
    any and all reserved character names'''
    if os.name == "nt": #Windows
        reserved_characters = ["<",">",":","\"","/","\\","|","?", "*"]
        for rs in reserved_characters:
            string = string.replace(rs, "")
        string = string.replace('–','-')
    else:
        string = string.replace(":", "").replace('–','-')
    
    return string

def saveAsSpreadsheet(lst_or_df, name_of_file):
    '''(<list or DataFrame> lst_or_df, <string> name_of_file)
    lst_or_df can be a list or dataframe data type. name_of_file, excluding the extention, i.e.: IMDB_Ratings-The_Office'''
    if type(lst_or_df) == list:
        df = pd.DataFrame(np.array(lst_or_df).T)
    else:
        df = lst_or_df

    child_dir = "data"
    if not os.path.exists(child_dir):
        os.makedirs(child_dir)

    new_path_and_filename = os.path.join(child_dir, safeFilenameFormat(name_of_file))+".csv"
    df.to_csv(new_path_and_filename, index=False)
        
    # Letting the User know where the file was saved
    print("The following file has been created:\n\t"+new_path_and_filename)
    return new_path_and_filename
    

def imdbScrapper(IMDB_URL):
    ''' (base_URL <string>)
    base_URL must look like the following "https://www.imdb.com/title/tt0068098/episodes?season=" as this will crawl 
    all the seasons within the show. Purposely skipping over seasons that are 
    Currently In Progress/Has Not Released/Has No Ratings Data Available or seasons with season numbers that are 
    literally Unknown

    Scraps the following data from the IMDB website:
        - Show Title
        - Season Number
        - Episode Number
        - Episode Title
        - Rating
        - Votes

    Creates a df of the scrapped data and saves them to a .csv file
    '''
    if IMDB_URL.find("imdb") == -1:
        sys.exit("URL is not an IMDB website")
    else:pass


    # In the event of IMDB giving a 400 code when scrapping 'byseasons', we can scrap 'byyear' instead.
    slash_list = []
    title_tt = re.findall('tt\d{7}', IMDB_URL)[0]

    base_URL = "https://www.imdb.com"

    base_content = requestContent(base_URL+"/title/"+title_tt)
    base_soup = BeautifulSoup(base_content, 'html.parser')
    soup_isy = base_soup.find("div", class_ = "seasons-and-year-nav")
    isy_urls_ext = [a['href'] for a in soup_isy.find_all('a', href=True) if a.text]

    ini_reqsts = 0
    scrap_type = None
    print("Attempting to Establish a good connection..")
    for isy_url_ext in isy_urls_ext:
        status = requests.get(base_URL+isy_url_ext).status_code
        ini_reqsts+=1
        print("Requests {} of possible {} ; status code {}\nURL {}".format(ini_reqsts, len(isy_urls_ext), status, base_URL+isy_url_ext))
        if status == 200:
            time.sleep(random.randint(8,15))
            if isy_url_ext.find("year") != -1:
                scrap_type = "year"
                break
            elif isy_url_ext.find("season") != -1:
                scrap_type = "season"
                break
        else:pass

    check_content = requestContent(base_URL+isy_url_ext)
    check_soup = BeautifulSoup(check_content, 'html.parser')

    # All the years or seasons found on IMDB for a certain show
    if scrap_type == "year" :
        years_or_seasons = check_soup.find("select", id = "byYear").text.split()
    elif scrap_type == "season" :
        years_or_seasons = check_soup.find("select", id = "bySeason").text.split()

    scrapping_URL = "https://www.imdb.com/title/{}/episodes?{}=".format(title_tt,scrap_type)#Able to limit to certain seasons if necessary

    # Due to psuedo crawling, this does not find the next URL in the HTML soup, but rather takes advantage of a URL pattern
    #   by appending a number to the end of the URL. In this case, we need to initialize the first URL
    initial_content = requestContent(scrapping_URL+years_or_seasons[0])
    initial_soup = BeautifulSoup(initial_content, 'html.parser')
    show_title = " ".join(initial_soup.find("h3", itemprop="name").text.split())

    # Where all the data will be stored ['SX', 'EX','Episode Title','Rating', 'Votes']
    data = []

    # Gives User a sense of progression
    reqsts = 0

    # episode number overall
    et = 0

    # Runs through each season
    for year_or_season in years_or_seasons: #year_or_season in years_or_seasons
        
        # Passes any season with the literal season number of 'Unknown'
        if year_or_season == 'Unknown':print("Year or Season # is 'Unknown'\nThis season has been skipped");continue
        else:pass
        
        # To prevent blockage of IP Address due to too many reqeusts
        time.sleep(random.randint(1,5))
        eta = ((len(years_or_seasons)-(reqsts+1 ))*((1+5.0)/2))
        
        # Gathering the Soup
        URL  = scrapping_URL+"{}".format(year_or_season)
        page_content = requestContent(URL)
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # Monitor the requests
        reqsts += 1
        print('Request:{} of {} made on {}; est. time remaining: {}s'.format(reqsts, len(years_or_seasons), time.ctime(time.time()), eta))

        # Soup Extractions
        try:
            sx_ex                = [i.text.split() for i in soup.find_all("div", class_ = "image")]                   #finds all seasons and episodes ['S1', 'Ep2']
            for i, elem in enumerate(sx_ex):                #reduces lists that look like this: ['Add', 'Image', 'S2,', 'Ep2'], to this ['S1', 'Ep2']
                if elem[0].lower() == "Add".lower() and len(elem) == 4:
                    sx_ex[i] = elem[2:]
            title                = [i.text.strip() for i in soup.find_all("a", itemprop = "name")]                    #finds all titles "Pilot"
            rating_and_votes     = [i.text.split() for i in soup.find_all("div", class_ = ["ipl-rating-star small","ipl-rating-star--placeholder"])]
            for i, elem in enumerate(rating_and_votes):
                if len(elem)   == 2:pass
                elif len(elem) == 1:
                    elem.append("(1)")
                    rating_and_votes[i]=elem
                elif len(elem) == 0:
                    rating_and_votes[i]=["N/A","N/A"]
            description          = [i.text.strip() for i in soup.find_all("div", class_ = "item_description")]        #finds all descriptions
            
            air_date             = []
            dates                = [i.text.strip().replace(".","") for i in soup.find_all("div", class_ = "airdate")]
            for date in dates:
                for dt_format_opt, dt_reformat_to in [["%b %Y","%m/01/%Y"], ["%Y", "01/01/%Y"], ["%d %b %Y","%m/%d/%Y"]]:
                    try:
                        air_date.append(datetime.strptime(date, dt_format_opt).strftime(dt_reformat_to))
                    except:pass                 #finds all air_dates 
        except ValueError:
            print("{} {} (Is In Progress/Has Not Released/Has No Ratings Data Available)\n{} {} has been skipped.".format(scrap_type.capitalize(), year_or_season,scrap_type.capitalize(), year_or_season))
            continue
            
        
        
        
        # Combining Soup Extractions into data
        if len(sx_ex) != len(rating_and_votes):
            print("{} {} (Is In Progress/Has Not Released/Has No Ratings Data Available)\n{} {} has been skipped.".format(scrap_type.capitalize(), year_or_season,scrap_type.capitalize(), year_or_season))
        else:
            for i in range(0, len(sx_ex)):
                et+=1
                data.append([
                            et,
                            re.sub('\D', '', sx_ex[i][0]), 
                            re.sub('\D', '', sx_ex[i][1]), 
                            title[i], 
                            rating_and_votes[i][0], 
                            rating_and_votes[i][1].replace("(","").replace(")",""),
                            air_date[i],
                            description[i]
                            ])

    # Creating and saving Dataframe 
    df = pd.DataFrame(data,columns=['ET','SX', 'EX','Episode Title','Rating', 'Votes', 'Air Date','Description'])
    path_and_filename = saveAsSpreadsheet(df, show_title + " - IMDB")
    return path_and_filename