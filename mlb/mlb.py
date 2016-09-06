import datetime
import json
import requests
import sys
from multiprocessing.dummy import Pool as ThreadPool

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
    score = game['linescore']
    print '----------------------'
    print '| {:3} | {:>2} | {:>2} | {:>2} |'.format(game['away_name_abbrev'], score['r']['away'], score['h']['away'], score['e']['away'])
    print '| {:3} | {:>2} | {:>2} | {:>2} |'.format(game['home_name_abbrev'], score['r']['home'], score['h']['home'], score['e']['home'])
    print '----------------------'
    print 'W: {}'.format(get_deciding_pitcher_line(game['winning_pitcher']))
    print 'L: {}'.format(get_deciding_pitcher_line(game['losing_pitcher']))

    if game['save_pitcher']['name_display_roster']:
        print 'S: {} ({})'.format(game['save_pitcher']['name_display_roster'], game['save_pitcher']['saves'])

def print_detailed_boxscore(game):
    score = game['linescore']
    print '----------------------'
    inning_numbers = [' {:>2} '.format(str(x)) for x in range(1, len(score['inning']) + 1)]
    away_runs =      [' {:>2} '.format(x['away']) for x in score['inning']]
    home_runs =      [' {:>2} '.format('' if x.get('home') is None else x['home']) for x in score['inning']]
    
    print '|'.join(inning_numbers)
    print '|'.join(away_runs)
    print '|'.join(home_runs)


day_count=1

pool = ThreadPool(day_count)
results = pool.map(get_scorecard, get_scorecard_urls(datetime.datetime.today(), day_count))

pool.close()
pool.join()

for result in results:
    for index, game in enumerate(result['game']):
        print str(index) + ')'
        print_boxscore(game)
        print ''
        print_detailed_boxscore(game)
        print ''

sys.exit(0)


