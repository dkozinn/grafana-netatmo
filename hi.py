#!/usr/bin/python3

# Heat Index: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
# Windchill: https://www.weather.gov/media/epz/wxcalc/windChill.pdf

from influxdb import InfluxDBClient

user="rvweather"
password="NWS-Upton"
dbname="scratch"
host="aws.kozinn.com"
module="calc"
station="K2DBK"

temp_query="select last(value) from temperature where module=~/Outdoor/"
hum_query="select last(value) from humidity where module=~/Outdoor/"
wind_query="select last(value) from windstrength where module=~/Outdoor/"

client = InfluxDBClient(host=host,username=user,password=password, database=dbname)

t=client.query(temp_query,epoch="ns")
h=client.query(hum_query,epoch="ns")

T=next(t.get_points())["last"]*1.8+32
timestamp=next(t.get_points())["time"]
RH=next(h.get_points())["last"]

if T < 50:                  # Calculate wind chill
    w=client.query(wind_query,epoch="ns")
    W=next(w.get_points())["last"]
    CHILL=((35.74+(0.6215 * T) - (35.75 * W**0.16) + (0.4275 * T * W**0.16))-32) * (5/9)   #Convert back to C to store
    print(timestamp, T, W, CHILL)
    lineout="chill,station="+station+",module=calc value="+str(CHILL)+" "+str(timestamp)

elif RH<40 or T < 80:
    exit    #No heat index at those conditions

else:       # Heat index
    HI_simple = 0.5 * (T + 61.0 + ((T-68.0)*1.2) + (RH*0.094))
    if (T+HI_simple)/2 > 80:
        HI = -42.379 + 2.04901523*T + 10.14333127*RH - .22475541*T*RH - .00683783*T*T - .05481717*RH*RH + .00122874*T*T*RH + .00085282*T*RH*RH - .00000199*T*T*RH*RH
    else:
        HI=HI_simple

    print(timestamp, T, RH, HI,HI_simple)

    lineout="hi,station="+station+",module=calc value="+str(HI)+" "+str(timestamp)
    
client.write_points(lineout,protocol='line')
