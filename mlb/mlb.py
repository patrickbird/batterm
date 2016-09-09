import argparse
import cmd
import datetime
import json
import requests
import shutil
import sys
from multiprocessing.dummy import Pool as ThreadPool




def create_empty_linescore():
    return {                
            'r': {
                'home': '',
                'away': ''
            },
            'h': {
                'home': '',
                'away': ''
            },
            'e': {
                'home': '',
                'away': ''
            }
    }

def get_scorecard_url(date_time):
    "Get the master scorecard URL of a given day."
    return 'http://m.mlb.com/gdcross/components/game/mlb/year_{0}/month_{1}/day_{2}/master_scoreboard.json'.format(date_time.year, str(date_time.month).zfill(2), str(date_time.day).zfill(2))

def get_scorecard_urls(date, count):
    return [get_scorecard_url(date - datetime.timedelta(days=x)) for x in range(count)]

def get_scorecard(url):
    return json.loads(requests.get(url).text)['data']['games']

def get_deciding_pitcher_line(pitcher):
    return '{} ({}, {}-{})'.format(pitcher['name_display_roster'], pitcher['era'], pitcher['wins'], pitcher['losses'])

def print_boxscore(game):
    boxscore = []
    score = game['linescore'] if 'linescore' in game else create_empty_linescore()
    boxscore.append('----------------------')
    boxscore.append('| {:3} | {:>2} | {:>2} | {:>2} |'.format(game['away_name_abbrev'], score['r']['away'], score['h']['away'], score['e']['away']))
    boxscore.append('| {:3} | {:>2} | {:>2} | {:>2} |'.format(game['home_name_abbrev'], score['r']['home'], score['h']['home'], score['e']['home']))
    boxscore.append('----------------------')
    boxscore.append('W: {}'.format(get_deciding_pitcher_line(game['winning_pitcher']))) if 'winning_pitcher' in game else ''
    boxscore.append('L: {}'.format(get_deciding_pitcher_line(game['losing_pitcher']))) if 'losing_pitcher' in game else ''

    if 'save_pitcher' in game and game['save_pitcher']['name_display_roster'] != '':
        boxscore.append('S: {} ({})'.format(game['save_pitcher']['name_display_roster'], game['save_pitcher']['saves']))

    return boxscore

def print_detailed_boxscore(game):
    score = game['linescore']
    print('----------------------')
    inning_numbers = [' {:>2} '.format(str(x)) for x in range(1, len(score['inning']) + 1)]
    away_runs =      [' {:>2} '.format(x['away']) for x in score['inning']]
    home_runs =      [' {:>2} '.format('' if x.get('home') is None else x['home']) for x in score['inning']]
    
    print ('|'.join(inning_numbers))
    print ('|'.join(away_runs))
    print ('|'.join(home_runs))

def print_boxscores(boxscores):
    terminal_size = shutil.get_terminal_size((80, 20))
    boxscore_columns = int(int(terminal_size.columns)/40)
    boxscore_rows = int(len(boxscores) / boxscore_columns)
    if len(boxscores) % boxscore_columns > 0:
        boxscore_rows += 1


    for i in range(0, boxscore_rows):
        for j in range(0, 8):
            for k in range(0, boxscore_columns):
                index = i * boxscore_columns + k
                if index >= len(boxscores):
                    print ('{:40}'.format(''), end='')
                elif j >= len(boxscores[index]):
                    print ('{:40}'.format(''), end='')
                else:
                    print ('{:40}'.format(boxscores[index][j]), end='')

                if k == boxscore_columns - 1:
                    print ('')

def get_scoreboards(day_count):
    pool = ThreadPool(day_count)
    results = pool.map(get_scorecard, get_scorecard_urls(datetime.datetime.today(), day_count))

    pool.close()
    pool.join()

    return results

'''
parser = argparse.ArgumentParser(description='Do some MLB stuff')
parser.add_argument('-t', '--team', help = 'the team to fetch')
parser.add_argument('-n', '--number', default = 1, help = 'the number of games to fetch')

subparsers = parser.add_subparsers(dest='subparser_name')

rhe_parser = subparsers.add_parser('rhe', help = 'rhe help')
line_parser = subparsers.add_parser('line', help = 'line help')

args = vars(parser.parse_args())
print(args)

if 'subparser_name' not in args:
    sys.exit(0)

if args['subparser_name'] == 'line':

    print('')

if args['subparser_name'] == 'rhe':
    for scoreboard in get_scoreboards(args['number']):
        boxscores = [print_boxscore(x) for x in scoreboard['game']]
        
        print('{}-{}-{}'.format(scoreboard['year'], scoreboard['month'], scoreboard['day']))
        print('')
        print_boxscores(boxscores)
        boxscores.clear()
        print('')
'''

class MlbShell(cmd.Cmd):
    intro = 'Welcome to the MLB shell.\n'
    prompt = '(mlb) '
    file = None

    def do_rhe(self, arg):
        for scoreboard in get_scoreboards(1):
            boxscores = [print_boxscore(x) for x in scoreboard['game']]
            
            print('{}-{}-{}'.format(scoreboard['year'], scoreboard['month'], scoreboard['day']))
            print('')
            print_boxscores(boxscores)
            boxscores.clear()
            print('')

    def do_quit(self, arg):
        return True
        

if __name__ == '__main__':
    MlbShell().cmdloop()


