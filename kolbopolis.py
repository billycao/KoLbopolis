#!/usr/bin/env python
"""Clan Dungeon History Parser"""

import sys
import os
import re
import urllib2
import yaml
import csv
from BeautifulSoup import BeautifulSoup

__author__  = 'Billy Cao'
__license__ = 'MIT'
__version__ = '0.1'
__status__  = 'Prototype'

# The URL of the clan old logs
# Set this to http://kingdomofloathing.com/ or http://127.0.0.1:60080/
# to disable the startup prompt.
KOL_URL     = ''
OLDLOGS_PAGE = 'clan_oldraidlogs.php?startrow='
VIEWLOG_PAGE = 'clan_viewraidlog.php'
LOG_REGEX   = '(.*?)\s+\(#(\d*)\)\s+line_regex\s+\((\d*)\s+turns*\)'

class DungeonLog():
    dungeonName = ''        # Name (type) of dungeon
    columns = {}            # dict of columns (set in *.yml)
    data = {}               # dict of rows
    score_equation = ''     # Equation for 'score' column (set in *.yml)

    def __init__(self,dungeonName):
        """Given a dungeon name, open settings YAML file and apply settings (ie. columns)"""
        self.dungeonName = dungeonName

        # Open and load dungeon YML
        f = open('dungeons/'+self.dungeonName+'.yml')
        settings = yaml.load(f.read())
        f.close()
        self.score_equation = settings['score']
        for column in settings['columns']:
            if 'id' in column and 'name' in column and 'val' in column:
                colid = column['id']
                self.columns[colid] = {'name': column['name'], 'val': column['val']}
            else:
                exit('ERROR: Column missing id, name, or value: \n'+column)

    def process_log(self,soup):
        """Given a BeautifulSoup object of a log page, traverse line by line
        and add the log data to self.data"""
        log = soup('blockquote')[0].contents

        for element in log:
            if element.string:
                log_row = str(element.string)   # The raw log line (eg. Bakaa is awesome (1 turn))
                log_row_data = []               # dict (colname, colid, playername, playerid, value)
                # Match log line with our catalog of columns
                for colid, column in self.columns.items():
                    regex = LOG_REGEX.replace('line_regex',column['val'])
                    m = re.search(regex, log_row)
                    if m:
                        try:
                            log_row_data = {
                                'colname'   : column['name'],
                                'colid'     : colid,
                                'playername': m.group(1),
                                'playerid'  : m.group(2),
                                'value'     : int(m.group(3)),
                            }
                        except ValueError:
                            exit('ERROR: The value of turns was not numerical:\n')
                            print log_row
                        break
                # Enter in this matched line into self.data
                if not log_row_data:
                    raw_input('WARNING: The following row was not recognized.'
                              + ' Press Enter to continue.\n' + log_row)
                else:
                    # Check if row for this user already exists in self.data
                    # If so, increment value for correct column
                    # If not, create the row and insert value into correct column
                    if log_row_data['playerid'] in self.data:
                        if log_row_data['colid'] in self.data[log_row_data['playerid']]:
                            self.data[log_row_data['playerid']][log_row_data['colid']] += log_row_data['value']
                        else:
                            self.data[log_row_data['playerid']][log_row_data['colid']] = log_row_data['value']
                    else:
                        self.data[log_row_data['playerid']] = {
                            'playername': log_row_data['playername'],
                            'playerid'  : log_row_data['playerid'],
                            log_row_data['colid'] : log_row_data['value']
                        }

        # Parse loot logs and append them to log_loot
        # Loot logs, because of their <b> tag, are grouped into 4s
        if len(soup('blockquote')) > 1:
            log_loot = []
            loot_line = ''
            for i,element in enumerate(soup('blockquote')[1].contents):
                if i % 4 == 3:
                    log_loot += [loot_line]
                    loot_line = ''
                elif element.string:
                    loot_line += element.string

            #TODO: Process loot logs

    def export_csv(self):
        """Creates a CSV export of the data in self.data"""
        # Prompt user for overwrite if file exists
        fileName = 'data/'+self.dungeonName+'.csv'
        if os.path.exists(fileName):
            while True:
                input = raw_input(fileName+' already exists. Overwrite? (y or n) ')
                if input == 'y' or input == 'Y':
                    break
                elif input == 'n' or input == 'N':
                    # If user chooses not to overwrite, generate unique filename
                    copyCounter = 1
                    while os.path.exists(fileName):
                        fileName = 'data/'+self.dungeonName+' ('+copyCounter+').csv'
                    break
        # Open file for writing
        print 'Writing data into '+fileName+'...'
        f = open(fileName,'wb')
        csvWriter = csv.writer(f)
        # Write columns
        row = ['Player','ID']
        for i,column in self.columns.items():
            row.append(column['name'])
        csvWriter.writerow(row)
        # Write data
        for id,user in self.data.items():
            row = [user['playername'], id]
            for i,column in self.columns.items():
                row.append(user[i] if i in user else 0)
            csvWriter.writerow(row)
        f.close()

class ClanLog():
    soup = None             # BeautifulSoup object of current log page being processed
    num_logs = 0            # Number of dungeon logs (From 'Showing 1-10 of XXX')
    log_ids = []            # List of dungeon log IDs
    dungeon_logs = []       # List of DungeonLog objects

    def __init__(self):
        """Open clan old logs page, create soup object from page data."""
        #TODO: Verify page format (in case the KoL devs changed something)
        print 'Opening '+KOL_URL+OLDLOGS_PAGE+'... '
        try:
            html = urllib2.urlopen(KOL_URL+OLDLOGS_PAGE)
            self.soup = BeautifulSoup(html)
            html.close()
        except:
            exit('ERROR: Could not resolve URL. Please check your connection.')
            raise
        print 'Success! Old log page opened.\n'
        # Get number of total logs
        found = self.soup.findAll(text=re.compile('Showing .*? of (\d*)'))
        match = re.match('Showing .*? of (\d*)',found[0])
        self.num_logs = int(match.group(1))
        # Get log_ids into self.log_ids
        self.get_logids()

    def get_logids(self):
        """Get clan log ids (eg. 114464) from "view logs" links."""
        #TODO: Insert code for multiple log pages
        print 'Extracting log IDs...'
        log_startrow = 0        # Log iterator for clan_oldraidlogs.php?startrow=
        while True:
            print 'Getting Log IDs '+str(log_startrow)+'-'+str(log_startrow+9)+'...'
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
            if len(self.soup.findAll(text="(No previous Clan Dungeon records found)")) > 0:
                break
            else:
                log_startrow += 10
                # Open next page
                try:
                    html = urllib2.urlopen(KOL_URL+OLDLOGS_PAGE+str(log_startrow))
                    self.soup = BeautifulSoup(html)
                    html.close()
                except:
                    exit('ERROR: Could not resolve URL: '+KOL_URL+OLDLOGS_PAGE+str(log_startrow)
                         + '\nPlease check your connection.')
                    raise

        if len(self.log_ids):
            print 'Success! '+str(len(self.log_ids))+' log IDs discovered.'
        else:
            exit('ERROR: No log IDs found. Are you logged in?')
            
    def process_logid(self, logid):
        try:
            html = urllib2.urlopen(KOL_URL+VIEWLOG_PAGE+'?viewlog='+str(logid))
            log_soup = BeautifulSoup(html)
            html.close()
        except:
            exit('ERROR: Could not access log #'+str(logid)+'.'
                 + 'Please check your connection.')
            raise

        # Get name (type) of Dungeon
        m = re.search('<center><b>(.*?) run, .*?</b></center>',
                      str(log_soup.html))
        dungeonName = m.group(1).replace(' ','_')

        # Create or get dungeon log
        if os.path.exists('dungeons/'+dungeonName+'.yml'):
            dungeonLog = None
            for dlog in self.dungeon_logs:
                if dlog.dungeonName == dungeonName:
                    dungeonLog = dlog
            if dungeonLog is None:
                dungeonLog = DungeonLog(dungeonName)
                self.dungeon_logs.append(dungeonLog)
            dungeonLog.process_log(log_soup)
        else:
            print 'Warning: '+dungeonName+'.yml not found. Skipping...'

    def export_csv(self):
        for dungeonLog in self.dungeon_logs:
            dungeonLog.export_csv()

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
    c = ClanLog()
    num_logids = len(c.log_ids)
    # Process log_ids
    for i,logid in enumerate(c.log_ids):
        print 'Processing log #'+str(logid)+'... ('+str(i+1)+'/'+str(num_logids)+')'
        c.process_logid(logid)
    c.export_csv()

if __name__ == '__main__':
    sys.exit(main())

