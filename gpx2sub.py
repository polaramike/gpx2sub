#! /usr/bin/python3
#
# GPX2SUB
#
# Script to enrich Flipper Zero SubGhz (.sub) files with geocoordinates by matching
# thr timestamp from the .sub file's filename against trackpoints from a GPX file.
# Besides latitude and longituse, a generated link to Google Maos is created
# and written to the .sub file as a comment.
#
# To have the .sub files named as needed by your Flipper Zero, you have to go to
# Settings->System->File Naming and set it to 'Time'. Since FZ files do not have a 
# real timestamp and the file gets the current date/time when transferred to a PC,
# this is a usable way. The format string for the date/time in the filename can
# be configured in the script.
#
# Usage:   gpx2sub.py gpx_file sub_file
# Example: gpx2sub data/mycurtrack.gpx /mnt/flipper/2024-08-19_16,07,54.sub
#
import sys
import gpxpy
import gpxpy.gpx
from pathlib import Path
from datetime import datetime, timezone
from geographiclib.geodesic import Geodesic

version = '0.2'

# configuration
#
# Adjust according to your needs. The defaults worked for me for the Momentum-005
# Flipper Zero firmware with european d/m/y date format and 24h clock. 
#
# start of timestamp in filename of the .sub file
timestart = 0
# length of timestamp in filename of the .sub file
timelen = 19
# Format of date & time in filename of the .sub file
timefmt = '%Y-%m-%d_%H,%M,%S'
# Here you can define the identifier/header for the latitude that gpx2sub writes into 
# the .sub file. The Momentum firmware writes 'Latitute' instead of 'Latitude', so
# here you can decide if you're compatible or correct :-D.
MMTMlat = 'Latitute'
#MMTMlat = 'Latitude'


# Got the interpolation function from 
# https://datascience.stackexchange.com/questions/113077/interpolate-a-point-in-time-for-two-given-geolocations-and-their-times-in-python
# and midified it a bit for this script.
def interpolate(lat1, lon1, lat2, lon2, time1, time2, time3):
    print('- interpolating coordinates')
    # convert datetime to seconds since epoch
    ts1 = time1.timestamp()
    ts2 = time2.timestamp()
    ts3 = time3.timestamp()
    # check validiry
    if lat1 == 0 or lon1 == 0 or time1 == time2:
        print('Timestamp out of range of GPX.')
        exit()
    # Get distance and direction between initial points
    inverse_result = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    distance = inverse_result['s12']
    angle = inverse_result['azi1']
    # Calculate new distance from the first point
    speed = distance / (ts2 - ts1)
    distance3 = speed * (ts3 - ts1)
    # Get new location
    direct_result = Geodesic.WGS84.Direct(lat1, lon1, angle, distance3)
    lat3 = direct_result['lat2']
    lon3 = direct_result['lon2']
    return lat3, lon3


def getfromgpx(gpxpath, flippath):
    print('- reading GPX file')
    # extract the pure filename from the .sub file's complete pathname
    flipname = Path(flippath).stem
    # extract timestamp from filename of .sub file,
    dtflip = flipname[timestart:timelen]
    # convert to a datetime type
    dtflip = datetime.strptime(dtflip,timefmt)
    # and finally convert it's timestamp to UTC, assuming it was saved in the local timezone
    dtfliputc = dtflip.astimezone(timezone.utc)
    # set lat and lon to a default
    lat = '0'
    lon = '0'
    # open the GPX file and try to find/interpolate a matching coordinate
    try:
        gpx_file = open(gpxpath, 'r')
    except FileNotFoundError:
        print(f"GPX file {gpxpath} not found!", file=sys.stderr)
        exit()
    except PermissionError:
        print(f"Insufficient permission to read {gpypath}!", file=sys.stderr)
        exit()
    except IsADirectoryError:
        print(f"{gpxpath} is a directory!", file=sys.stderr)
        exit()
    gpx = gpxpy.parse(gpx_file)
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                #pointbef = point
                # explicitly set the timezone of the point's timestamp to UTC
                point.time =  point.time.replace(tzinfo=timezone.utc)
                # At this point, all the datetime variables should be UTC
                # and thus logically and syntactically comparable...
                #
                # time matches exactly with a trackpount
                if dtfliputc == point.time:
                    lat = point.latitude
                    lon = point.longitude
                    break
                # the time of the trackpoint is later than the timestamp of our file
                if point.time > dtfliputc:
                    pointaft = point
                    lat, lon = interpolate(pointbef.latitude, pointbef.longitude, pointaft.latitude, pointaft.longitude, pointbef.time, pointaft.time, dtfliputc)
                    break
                # remember this trackpoint as the one before the next point
                pointbef = point
    # If the timestamp of the .sub is not in the .gpx, just exit.
    if lat == '0' or lon == '0':
        print('Timestamp not found in GPX track.')
        exit()
    return lat, lon                


def updatesub(flippath, flat, flon):
    print('- updating .sub file')
    # read the contents of the .sub file
    try:
        with open(flippath, 'rt') as flipfile:
            lines = [line.rstrip() for line in flipfile]
    except FileNotFoundError:
        print(f"File {flippath} not found!", file=sys.stderr)
        exit()
    except PermissionError:
        print(f"Insufficient permission to read {flippath}!", file=sys.stderr)
        exit()
    except IsADirectoryError:
        print(f"{flippath} is a directory!", file=sys.stderr)
        exit()
    flipfile.close()
    # now write it back, adding/updating the coordinates
    try:
        flipfile = open(flippath, 'wt')
    except PermissionError:
        print(f"Insufficient permission to write {flippath}!", file=sys.stderr)
        exit()
    for line in lines:
        # Omit latitude/longitude lines if already present,  Since somebody had
        # a typo ('Latitute') in Momentum, we have to check foe it as well. And
        # since we include a link to Google Maps, we check that, too.
        if not 'itude' in line and not 'itute' in line and not 'google' in line:
            # place Lat/Lon before the 'Ptotocol' line
            if 'Protocol' in line:
                flipfile.write(MMTMlat+': '+str(flat)+'\n')
                flipfile.write('Longitude: '+str(flon)+'\n')
            flipfile.write(line+'\n')
    # write a Google Maps link as comment at the end of the file
    flipfile.write('# https://www.google.com/maps/@'+str(flat)+','+str(flon)+',50m\n')
    flipfile.close()

    
# ----- main -----
print('gpx2sub. v',version,' by polaramike')
# command line parms
if len(sys.argv) < 3:
    print('Usage: ', sys.argv[0], ' gpx_file sub_file')
    print('Example : ', sys.argv[0], ' data/mycurtrack.gpx /mnt/flipper/2024-08-19_16,07,56_Nexus-TH.sub\n')
    exit()
gpxarg = sys.argv[1]
subarg = sys.argv[2]
# Try to get coordinates from the GOX file
lat, lon = getfromgpx(gpxarg, subarg)
# now let's update the .sub file
updatesub(subarg, lat, lon)
print('- Done - have a nice day!\n')

# Congratulations, you chose to clean the elevator ...
