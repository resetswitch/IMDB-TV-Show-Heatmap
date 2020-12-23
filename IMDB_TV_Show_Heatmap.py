import pandas as pd
import numpy as np
import re
import os
import textwrap
import plotly.figure_factory as ff
import plotly.io as pio
import IMDB_Scrapper as scrap
pio.renderers.default='browser'

def EpisodeStatement(df):
    """
    for every episode in df, adds a episode statement string "Rated {'Rating'}; S{'SX'}E{'EX'} {'Episode Title'}"

    Parameters
    ----------
    df : Pandas DataFrame
        a df that has these columns
        - Season Number ('SX')
        - Episode Number ('EX')
        - Episode Title ('Episode Title')
        - Rating ('Rating')

    Returns
    -------
    ls : list of strings
        list of episodes as a statement
    """

    ls = []
    for index, row in df.iterrows():
        if len(row['Episode Title']) > 45:
            et = row['Episode Title'][:42] + "..."
        else:
            et = row['Episode Title']
        ls.append("Rated {}; S{}E{} {}".format(row['Rating'], str(row['SX']).zfill(2), str(row['EX']).zfill(2), et))
    return ls


def creatingImdbHeatmap(path_and_filename):
    """
    Data is taken from the .csv and converted into a heatmap

    Parameters
    ----------
    path_and_filename : string
        Takes in a .csv filename path from (example: "C:/Users/user/Desktop/IMDB_Ratings-The_Office_(2005-2013).csv")
    """      

    # Reading the .csv in to a Dataframe
    df = pd.read_csv(path_and_filename)

    # Finding the name of the Chart by the name of the filename
    basename = os.path.basename(path_and_filename)
    chart_title = os.path.splitext(basename)[0]  

    # Finding the top and bottom N episodes
    N = 3
    top_N = df.nlargest(N, ['Rating']) 
    bot_N = df.nsmallest(N, ['Rating']) 
    top_N_ratings = top_N['Rating'].values
    bot_N_ratings = bot_N['Rating'].values
    top_N_rating_statements = EpisodeStatement(top_N)
    bot_N_rating_statements = EpisodeStatement(bot_N)
    print("Best Episodes\n" +"\n".join(top_N_rating_statements))
    print("Worst Episodes\n"+"\n".join(bot_N_rating_statements))

    # Defining constants
    pad_rating = 0                  #value with which to pad the lists
    max_rating = 10

    # Finds the total number of seasons
    seasons_max  = df['SX'].max()

    # Finding the number of episodes in each Season
    num_ep_within_season = df['SX'].value_counts().sort_index()                                          

    # Finding the Season with the most Episodes, and making that a demension d
    d = num_ep_within_season.max()

    # Preparing the columns in DataFrame
    rect_data_number        = pd.DataFrame(columns=["Ep."+str(i) for i in range(1,d+1)])
    rect_data_label         = pd.DataFrame(columns=["Ep."+str(i) for i in range(1,d+1)])
    rect_data_title         = pd.DataFrame(columns=["Ep."+str(i) for i in range(1,d+1)])
    rect_data_airdate       = pd.DataFrame(columns=["Ep."+str(i) for i in range(1,d+1)])
    rect_data_description   = pd.DataFrame(columns=["Ep."+str(i) for i in range(1,d+1)])

    # Separating the Data Seasonaly and Rectangularizing (padding) with Zero's and Empty strings for Labels
    for i in range(1, seasons_max+1):
        seasons_ratings = df[df['SX'].isin([i])]['Rating'].values.tolist()
        rating_label    = seasons_ratings.copy()
        rating_number   = seasons_ratings.copy()
        title           = df[df['SX'].isin([i])]['Episode Title'].values.tolist()
        airdate         = df[df['SX'].isin([i])]['Air Date'].values.tolist()
        description     = df[df['SX'].isin([i])]['Description'].values.tolist()
        for _ in range(len(seasons_ratings),d):
            rating_label.append("")
            rating_number.append(0)
            title.append("DNE")
            airdate.append("")
            description.append("")

        for idx, string in enumerate(description):
            new_string = "<br>".join(textwrap.wrap("Description: "+string, width=30))
            description[idx] = new_string

        rect_data_number.loc['Season {}'.format(i)]     = rating_number
        rect_data_label.loc['Season {}'.format(i)]      = rating_label
        rect_data_title.loc['Season {}'.format(i)]      = title
        rect_data_airdate.loc['Season {}'.format(i)]    = airdate
        rect_data_description.loc['Season {}'.format(i)]= description

    vals = rect_data_number.values.tolist()[::-1]
    cols = rect_data_number.columns.tolist()
    idxs = rect_data_number.index.tolist()[::-1]
    z_l = rect_data_label.values.tolist()[::-1]

    titles = rect_data_title.values.tolist()[::-1]
    airdates = rect_data_airdate.values.tolist()[::-1]
    descriptions = rect_data_description.values.tolist()[::-1]

    hover=[]
    for row in range(len(z_l)):
        hover.append(['Season: ' + re.findall(r'\d+', idxs[row])[0] + ', Ep: ' + ep + '<br>' + 
                        'Ep Title: ' + title + '<br>' + 
                        'Air Date: ' + airdate + '<br>' + 
                        'Rating: ' + str(z_l_i) + '<br>' + 
                        description
                        for z_l_i, title, ep , airdate, description in zip(z_l[row], titles[row], [re.findall(r'\d+', col)[0] for col in cols], airdates[row], descriptions[row])])

    # Set Colorscale
    colorscale=[[0.0, 'rgb(255,255,255)'], [.01, 'rgb(255, 77, 148)'],
                [.25, 'rgb(240, 179, 255)'], [.5, 'rgb(255, 255, 153)'],
                [.75, 'rgb(179, 217, 255)'],[1.0, 'rgb(0, 255, 128)']]


    fig = ff.create_annotated_heatmap(vals, x=cols, y=idxs,  annotation_text=z_l, colorscale=colorscale, text=hover, hoverinfo='text',
                                        showscale = True, zmax=10, zmin=df['Rating'].min()-.1, colorbar = dict(thickness=25, ypad = 0),
                                        font_colors=['rgb(0, 0, 0)','rgb(0, 0, 2)'])

    fig.add_annotation  (dict(font=dict(color="black",size=8),x=.1,y=-.2,align = "left",showarrow=False,
                        text="<b>Worst Episodes</b><br>"+"<br>".join(bot_N_rating_statements),textangle=0,xref="paper",yref="paper"))

    fig.add_annotation(dict(font=dict(color="black",size=8),x=.9,y=-.2,align = "left",showarrow=False,
                        text="<b>Best Episodes</b><br>"+"<br>".join(top_N_rating_statements),textangle=0,xref="paper",yref="paper"))

    fig.update_layout(xaxis_title="Episode", yaxis_title="Season", legend_title="IMDB Rating", margin_b=90, paper_bgcolor="white",
                        font=dict(family="Arial",size=8, color="Black"))

    fig.update_layout(title={"text": "<span style='font-size: 25px;'>{}</span><br>IMDB TV Show Episode Ratings Heatmap".format(chart_title.replace("_"," ").replace("-", "-")).replace(' - IMDB',''),'y': .90},font=dict(family="Arial",size=8, color="Black"))
    print('Plot opening in default browser')
    fig.show()



filename = scrap.imdbScrapper("https://www.imdb.com/title/tt0206512/?ref_=fn_al_tt_1")
creatingImdbHeatmap(filename)
