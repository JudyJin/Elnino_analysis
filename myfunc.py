9import numpy as np
import matplotlib.pyplot as plt
from IPython.display import Image
import pandas as pd
from matplotlib import cm
import os

import cartopy
import cartopy.crs as ccrs
from cartopy import config
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy import feature as cfeature
from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, OCEAN, LAKES, BORDERS

import requests

def get_data(year, month_start, month_end):
    # acquire dataset using api
    # citation: https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation
    """
    Given a year, start month and end month, get the detail global marine data for every 10 days.
    Then write the data as csv file, the filename as the date.
    
    Parameters: 
    year: the year we want to aquire data for
    month_start: the starting month in the given year
    month_end: the ending month in the given year
    
    Returns: 
    None
    """
    # creat the time range for the given parameter
    if month_end == 12:
        rang = list(pd.date_range(start = str(month_start)+"/1/"+str(year), 
                                  end = "1/1/"+str(year+1)))
    else:
        rang = list(pd.date_range(start = str(month_start)+"/1/"+str(year), 
                                  end = str(month_end+1)+"/1/"+str(year)))
    
    # api endpoint 
    endpoint = "https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-marine&\
    dataType=AIR_TEMP&startDate={}&boundingBox=90,-180,-90,180&format=csv"
    
    # get data request for every 10 days
    for i in range(0,len(rang),10):
        date = str(rang[i].date())
        resp = requests.get(endpoint.format(date+"&endDate="+date))
        
        # write the requested data into csv
        f = open(date+".csv", "w")
        f.write(resp.text)
        f.close()
      
    # return nothing 
    return None

def read_table(filename):
    """
    Read in and reduce table
    Parameters: 
        file: the filename we want to read in
    Return: 
        a table with column 'LATITUDE', 'LONGITUDE', 'AIR_TEMP', 'WIND_DIR', 'WIND_SPEED', 'SEA_SURF_TEMP',
        'SEA_LVL_PRES'
    """
    # the column list I want to read in 
    col_list =['LATITUDE', 'LONGITUDE', 
               'AIR_TEMP', 'WIND_DIR', 'WIND_SPEED', 'SEA_SURF_TEMP', 'SEA_LVL_PRES']
    # read in table with only the above column list
    df = pd.read_csv(filename, usecols = col_list)
    
    # make all latitude and longitude into to int (will reduce later table size)
    df["LATITUDE"] = df["LATITUDE"].astype(int)
    df["LONGITUDE"] = df["LONGITUDE"].astype(int)
    
    # according to the documentation, tempeture is at tenth of the celsius
    df["AIR_TEMP"] = df["AIR_TEMP"]/10
    df["SEA_SURF_TEMP"] = df["SEA_SURF_TEMP"]/10
    df["SEA_LVL_PRES"] = df["SEA_LVL_PRES"]/10
    # return the table 
    return df

def global_map(file,date,element):
    """
    Generates a global map of the desired geomagnetic element.  
    Parameters: 
        file: the filename we want to read in
        date: corresponding date for the file
        element: desired element for the map
            Allowed elements are:
            AIR_TEMP (air temperture),
            SEA_SURF_TEMP (sea surface temperature), 
            SEA_LVL_PRES (sea level pressure)
    Return: 
        None
    """
    # read in table
    df = read_table(file)
    df = df.dropna(subset = [element])
    df = df.groupby(["LATITUDE","LONGITUDE"],as_index = False)[element].mean()
    
    #print(df[element].min(),df[element].max())
    # set title and vmin and vmax according to the data
    if element=='AIR_TEMP':
        title='Air Temperature (C)'
        mi = -10
        ma = 35
    elif element=='SEA_SURF_TEMP':
        title='Sea Surface Temperature (C)'
        mi = 3
        ma = 33
    elif element=='SEA_LVL_PRES':
        title = 'Presure (hPa_millibars)'
        mi = 960
        ma = 1040
        
    # make the map
    plt.clf() #clear the plot to avoid seeing multiple times
    ax1 = plt.axes(projection=ccrs.PlateCarree(central_longitude=160.0))
    ax1.add_feature(OCEAN,color='lightblue')
    ax1.add_feature(LAND,color='orange')
    ax1.coastlines();
    # plot the data point 
    plt.scatter(df.LONGITUDE,df.LATITUDE,c=df[element],
                vmin = mi, vmax = ma,transform=ccrs.PlateCarree());
    plt.colorbar(orientation="horizontal",spacing = "uniform")
    ax1.set_global();
    # assigns title

  
    plt.title(title+": "+date); 
    if element not in os.listdir():
        os.mkdir(element)
    plt.savefig(element+'/'+title+'_'+date+'.png') # saves the  figure. to a folder
    return None

def diff_map(before,after,element):
    """
    Generates a global map of the desired geomagnetic element.  
    Parameters: 
        file: the filename we want to read in
        date: corresponding date for the file
        element: desired element for the map
            Allowed elements are:
            AIR_TEMP (air temperture),
            SEA_SURF_TEMP (sea surface temperature), 
            SEA_LVL_PRES (sea level pressure)
    Return: 
        None
    """
    
    # read in table (all table for the month)
    filenames=sorted(os.listdir('data/')) 
    df1 = []
    df2 = []
    for file in filenames:
        if file[:7] == before:
            if len(df1) == 0:
                df1 = read_table('data/'+file)
            else:
                df1 = df1.append(read_table('data/'+file))
        elif file[:7] == after:
            if len(df2) == 0:
                df2 = read_table('data/'+file)
            else:
                df2 = df2.append(read_table('data/'+file))
    
    # do some modification to the table
    df1 = df1.dropna(subset = [element])
    df1 = df1.groupby(["LATITUDE","LONGITUDE"],as_index = False)[element].mean()
    df2 = df2.dropna(subset = [element])
    df2 = df2.groupby(["LATITUDE","LONGITUDE"],as_index = False)[element].mean()
    
    diff = df1.merge(df2,on = ["LATITUDE","LONGITUDE"],suffixes=[before[:4], after[:4]])
    diff[element+"_diff"] = diff[element+after[:4]] - diff[element+before[:4]]

    # assigns title
    if element=='AIR_TEMP':
        title='Air Temperature (C)'
        mi = -3
        ma = 3
    elif element=='SEA_SURF_TEMP':
        title='Sea Surface Temperature (C)'
        mi = -3
        ma = 3
    elif element=='SEA_LVL_PRES':
        title = 'Pressure (hPa_millibars)'
        mi = -20
        ma = 20
  
    
    # make the map
    # plot point plot with geoplot

    plt.clf() #clear the plot to avoid seeing multiple times
    plt.figure(figsize = (10,5))
    ax1 = plt.axes(projection=ccrs.PlateCarree(central_longitude=160.0))
    ax1.add_feature(OCEAN,color='lightblue')
    ax1.add_feature(LAND,color='orange')
    ax1.coastlines();
    
    # plot the diff graph
    plt.scatter(diff.LONGITUDE,diff.LATITUDE,c=diff[element+"_diff"],
                vmin = mi, vmax = ma, cmap='RdGy_r',transform=ccrs.PlateCarree());
    plt.colorbar(orientation="horizontal",extend ="both",spacing = "uniform")

    ax1.set_global();
    # plot title
    plt.title(title+" difference:"+before+'-'+after); 
    # save image
    if element not in os.listdir():
        os.mkdir(element)
    plt.savefig(element+'/'+title+'_month_'+after[5:7]+'.png') # saves the  figure. to a folder
    return None


# helper function to plot wind
def to_uv(winddir, windspeed):
    """
    Find u and v vector given wind direction and speed
    Parameters: 
        winddir: wind direction (0-360)
        windspeed: wind speed 
    Return:
        the corresponding u and v
    """
    u = np.cos(90-winddir)*windspeed
    v = np.sin(90-winddir)*windspeed
    return u,v


def plotwind(date):
    """
    Generates a global map of the wind of given date
    Parameters: 
        file: the filename we want to read in
        title: the date of the map  
    Return: 
        None
    """
    filenames=sorted(os.listdir('data/')) 
    df = []
    for file in filenames:
        if file[:7] == date:
            if len(df) == 0:
                df = read_table('data/'+file)
            else:
                df = df.append(read_table('data/'+file))
    # drop all nans
    df = df.dropna(subset = ["WIND_DIR","WIND_SPEED"])
    # find u and v
    df["u"],df["v"] = to_uv(df["WIND_DIR"],df["WIND_SPEED"])
    df = df.groupby(["LATITUDE","LONGITUDE"],as_index = False)["u","v"].mean()

          
    plt.clf()
    plt.figure(figsize = (10,5))
    ax1 = plt.axes(projection=ccrs.PlateCarree(central_longitude=50.0))
    ax1.add_feature(OCEAN,color='lightblue')
    ax1.add_feature(LAND,color='orange')
    ax1.coastlines();
    # using quiver function to plot the arrow
    plt.quiver(np.array(df.LONGITUDE),np.array(df.LATITUDE),
               np.array(df["u"]),np.array(df["v"]),color='k',transform=ccrs.PlateCarree(),norm = True);
    ax1.set_global();
    plt.title("Wind map: "+date); 
    plt.savefig("Wind/"+date+'.png',quality = 95) # saves the  figure. to a folder
    return None #Image(filename="Wind/"+date+'.png')