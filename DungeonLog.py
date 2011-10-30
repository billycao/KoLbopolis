import yaml
import re
import os
import csv

__author__ = 'billy'


class DungeonLog():
    LOG_REGEX   = '(.*?)\s+\(#(\d*)\)\s+line_regex\s+\((\d*)\s+turns*\)'
    
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
                    regex = self.LOG_REGEX.replace('line_regex',column['val'])
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