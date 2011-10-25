#!/usr/bin/env python
"""Clan Dungeon History Parser"""

import sys
import re
import urllib2
import yaml
from BeautifulSoup import BeautifulSoup

__author__  = 'Billy Cao'
__license__ = 'GPL'
__version__ = '0.1'
__status__  = 'Prototype'

# The URL of the clan old logs
OLDLOGS_URL = 'http://127.0.0.1:60080/clan_oldraidlogs.php'
VIEWLOG_URL = 'http://127.0.0.1:60080/clan_viewraidlog.php'

class DungeonLog():
    soup = None
    dungeonName = ''
    columns = []
    data = {}
    score_equation = ''

    def __init__(self,dungeonName):
        self.dungeonName = dungeonName

        # Open and load dungeon YML
        f = open('dungeons/'+self.dungeonName+'.yml')
        settings = yaml.load(f.read())
        f.close()
        self.score_equation = settings['score']
        for column in settings['columns']:
            colid = column['id'] if 'id' in column else ''
            if column['name'] and column['val']:
                self.columns.append([colid, column['name'], column['val']])
            else:
                exit('ERROR: Column missing name or value: \n'+column)

class ClanLog():
    soup = None
    log_ids = []
    dungeon_logs = []
    dungeon_names = []

    def __init__(self):
        """Open clan old logs page, create soup object from page data."""
        #TODO: Verify page format
        print 'Opening '+OLDLOGS_URL+'... '
        try:
            html = urllib2.urlopen(OLDLOGS_URL)
            self.soup = BeautifulSoup(html)
            html.close()
        except:
            exit('ERROR: Could not resolve URL. Please check your connection.')
            raise
        print 'Success! Old log page opened.\n'
    def get_logids(self):
        """Get clan log ids (eg. 114464) from "view logs" links."""
        #TODO: Insert code for multiple log pages
        print 'Extracting log IDs...'
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
        if len(self.log_ids):
            print 'Success! '+str(len(self.log_ids))+' log IDs discovered.'
        else:
            exit('ERROR: No log IDs found. Are you logged in?')
    def process_logid(self, logid):
        try:
            html = urllib2.urlopen(VIEWLOG_URL+'?viewlog='+str(logid))
            log_soup = BeautifulSoup(html)
            html.close()
        except:
            exit('ERROR: Could not access log #'+str(logid)+'.'
                 + 'Please check your connection.')
            raise

        # Get name of Dungeon
        m = re.search('<center><b>(.*?) run, .*?</b></center>',
                       str(log_soup.html))
        dungeonName = m.group(1).replace(' ','_')

        # Create or get dungeon log
        dungeonLog = None
        for i,name in enumerate(self.dungeon_names):
            if name == dungeonName:
                dungeonLog = self.dungeon_logs[i]
        if dungeonLog is None:
            self.dungeon_names.append(dungeonName)
            dungeonLog = DungeonLog(dungeonName)
            self.dungeon_logs.append(dungeonLog)

def main(argv=None):
    #TODO: Command line arguments
    if argv is None:
        argv = sys.argv

    # Connect to oldlogs.php, get log ids
    c = ClanLog()
    c.get_logids()
    num_logids = len(c.log_ids)
    for i,logid in enumerate(c.log_ids):
        #TODO: Inititialize dungeon, find dungeon type
        print 'Processing log #'+str(logid)+'... ('+str(i+1)+'/'+str(num_logids)+')'
        c.process_logid(logid)
        #TODO: Use dungeon object to calculate loot information
        #TODO: Export data into csv
        

if __name__ == '__main__':
    sys.exit(main())

