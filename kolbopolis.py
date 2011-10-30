#!/usr/bin/env python
"""Clan Dungeon History Parser"""

import sys
import ClanLog

__author__  = 'Billy Cao'
__license__ = 'MIT'
__version__ = '0.1'
__status__  = 'Prototype'

KOL_URL = ''

def main(argv=None):
    #TODO: Command line arguments
    # -l [log number]   - Specific log number to process
    # -p [port]         - Port of KoLmafia relay browser
    # -d|--dungeon [haunted:hobopolis:slime] - Dungeon to process
    # -v|--verbose      - Verbose output
    if argv is None:
        argv = sys.argv

    # Prompt user for KOL_URL if not already provided
    global KOL_URL
    while not KOL_URL:
        input = raw_input('Are you using KoLmafia (relay browser)? (y or n): ')
        if input == 'y' or input == 'Y':
            KOL_URL = 'http://127.0.0.1:60080/'
        elif input == 'n' or input == 'N':
            exit('ERROR: This has not yet been implemented.')
            # KOL_URL = 'http://kingdomofloathing.com/'

    # Connect to oldlogs.php, get log ids
    c = ClanLog(KOL_URL)
    num_logids = len(c.log_ids)
    # Process log_ids
    for i,logid in enumerate(c.log_ids):
        print 'Processing log #'+str(logid)+'... ('+str(i+1)+'/'+str(num_logids)+')'
        c.process_logid(logid)
    c.export_csv()

if __name__ == '__main__':
    sys.exit(main())

