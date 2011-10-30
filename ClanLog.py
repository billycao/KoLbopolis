import urllib2
import os
import re
import DungeonLog
from BeautifulSoup import BeautifulSoup

__author__ = 'billy'

class ClanLog():
    KOL_URL     = ''
    OLDLOGS_PAGE = 'clan_oldraidlogs.php?startrow='
    VIEWLOG_PAGE = 'clan_viewraidlog.php'

    soup = None             # BeautifulSoup object of current log page being processed
    num_logs = 0            # Number of dungeon logs (From 'Showing 1-10 of XXX')
    log_ids = []            # List of dungeon log IDs
    dungeon_logs = []       # List of DungeonLog objects


    def __init__(self):
        """Open clan old logs page, create soup object from page data."""
        #TODO: Verify page format (in case the KoL devs changed something)
        print 'Opening '+self.KOL_URL+self.OLDLOGS_PAGE+'... '
        try:
            html = urllib2.urlopen(self.KOL_URL+self.OLDLOGS_PAGE)
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
                    html = urllib2.urlopen(self.KOL_URL+self.OLDLOGS_PAGE+str(log_startrow))
                    self.soup = BeautifulSoup(html)
                    html.close()
                except:
                    exit('ERROR: Could not resolve URL: '+self.KOL_URL+self.OLDLOGS_PAGE+str(log_startrow)
                         + '\nPlease check your connection.')
                    raise

        if len(self.log_ids):
            print 'Success! '+str(len(self.log_ids))+' log IDs discovered.'
        else:
            exit('ERROR: No log IDs found. Are you logged in?')

    def process_logid(self, logid):
        try:
            html = urllib2.urlopen(self.KOL_URL+self.VIEWLOG_PAGE+'?viewlog='+str(logid))
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