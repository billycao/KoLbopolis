#!/usr/bin/env python
"""Clan Dungeon History Parser"""

import sys
import re
import urllib2
from BeautifulSoup import BeautifulSoup

__author__  = 'Billy Cao'
__license__ = 'GPL'
__version__ = '0.1'
__status__  = 'Prototype'

# The URL of the clan old logs
URL_STR = 'http://127.0.0.1:60080/clan_oldraidlogs.php'

class ClanLog():
    soup = None
    log_ids = []

    def __init__(self):
        # Get data from clan logs
        #TODO: Verify page format
        print 'Opening '+URL_STR+'...\n'
        try:
            html = urllib2.urlopen(URL_STR)
            self.soup = BeautifulSoup(html)
        except urllib2.URLError:
            exit('ERROR: Could not resolve URL. Please check your connection.')
    def get_logids(self):
        """Get clan log ids (eg. 114464) from "view logs" links."""
        for td in self.soup.findAll('td', {'class': 'tiny'}):
            open_bracket, link_tag, close_bracket = td.contents[:3]
            for attr,value in link_tag.attrs:
                if attr=='href':
                    id = re.search('clan_viewraidlog\\.php\?viewlog=(\\d+)',
                                   value)
                    # Store id in self.log_ids
                    try:
                        self.log_ids.append(int(id.group(1)))
                    except ValueError:
                        exit('ERROR: Invalid ID parsed. Log format may have '
                             + 'changed.')



def main(argv=None):
    #TODO: Command line arguments
    if argv is None:
        argv = sys.argv

    log = ClanLog()
    log.get_logids()

if __name__ == '__main__':
    sys.exit(main())

    