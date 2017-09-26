"""
Usage: collection_watcher.py --collection=<collection_id> --threshold=<hours> --notify=<email>
"""

from datetime import datetime
import time
from docopt import docopt

from blackfynn import Blackfynn
from blackfynn import Collection

arguments = docopt(__doc__)

bf = Blackfynn()
collection = bf.get(arguments['--collection'])
current_timestamp = time.time() * 1000

for item in collection.items:
    milliseconds_old = current_timestamp - int(item.get_property('created').value)
    hours_old = (milliseconds_old / (1000*60*60)) % 24
    if hours_old > int(arguments['--threshold']):
        print "send notification"
