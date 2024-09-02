# gpx2sub for FlipperZero SubGhz
Geotag Flipper Zero SubGhz files with a GPX track


This is a Script to enrich Flipper Zero SubGhz (.sub) files with geocoordinates by matching
thr timestamp from the .sub file's filename against trackpoints from a GPX file.
Besides latitude and longituse, a generated link to Google Maos is created
and written to the .sub file as a comment.

To have the .sub files named as needed by your Flipper Zero, you have to go to
Settings->System->File Naming and set it to 'Time'. Since FZ files do not have a 
real timestamp and the file gets the current date/time when transferred to a PC,
this is a usable way. The format string for the date/time in the filename can
be configured in the script.

## Usage

gpx2sub.py gpx_file sub_file

Example: gpx2sub data/mycurtrack.gpx /mnt/flipper/2024-08-19_16,07,54.sub

## Issues

Not each and every possible error is caught, but I guess the most common ones are. There
won't be a catastrophe if you encounter one of the uncaught errors, but as always, a
backup is a good idea.

My Python skills are limited and I'm sure this could be coded more elegant. For me,
the main goal is and was that it does what it's supposed to do.

## License
[MIT](https://choosealicense.com/licenses/mit/)
