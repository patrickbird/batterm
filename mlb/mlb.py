import argparse
import cmd
import datetime
import json
import requests
import shutil
import sys
from multiprocessing.dummy import Pool as ThreadPool

class ScoreboardManager:
    _scoreboards = {}

    def get_scoreboard(date):
        dates=[]
        for new_date in ScoreboardManager._get_date_range(date):
            if new_date not in ScoreboardManager._scoreboards:
                dates.append(new_date)

        if len(dates) > 0 and date not in ScoreboardManager._scoreboards:
            ScoreboardManager._scoreboards.update([(s.date, s) for s in ScoreboardManager._get_scoreboards(dates)])

        return ScoreboardManager._scoreboards[date]

    def _get_date_range(date):
        return [date + datetime.timedelta(days=1) - datetime.timedelta(days=x) for x in range(3)]

    def _get_scoreboards(dates):
        pool = ThreadPool(len(dates))

        results = pool.map(Scoreboard, dates)

        pool.close()
        pool.join()

        return results

class Scoreboard:
    def __init__(self, date):
        self.date = date
        self.url = self._get_scoreboard_url()
        self.scoreboard = self._get_scoreboard_dictionary()

    def _create_empty_linescore():
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
        
    def _get_scoreboard_url(self):
        "Get the master scorecard URL of a given day."
        return 'http://m.mlb.com/gdcross/components/game/mlb/year_{0}/month_{1}/day_{2}/master_scoreboard.json'.format(self.date.year, str(self.date.month).zfill(2), str(self.date.day).zfill(2))

    def _get_scoreboard_dictionary(self):
        return json.loads(requests.get(self.url).text)['data']['games']

    def get_deciding_pitcher_line(self, pitcher):
        return '{} ({}, {}-{})'.format(pitcher['name_display_roster'], pitcher['era'], pitcher['wins'], pitcher['losses'])

    def get_boxscores(self):
        return [self.get_boxscore(x) for x in self.scoreboard['game']]

    def get_boxscore(self, game):
        boxscore = []
        score = game['linescore'] if 'linescore' in game else self._create_empty_linescore()
        status = game['status']['status']

        if status != 'In Progress':
            boxscore.append(status)
        else:
            boxscore.append(game['status']['inning_state'][:3] + ' ' + game['status']['inning'])
            boxscore[-1] += '  {}-{}, {} {}'.format(game['status']['b'], game['status']['s'], game['status']['o'], 'Outs' if int(game['status']['o']) != 1 else 'Out')

        boxscore.append('----------------------')
        boxscore.append('| {:3} | {:>2} | {:>2} | {:>2} |'.format(game['away_name_abbrev'], score['r']['away'], score['h']['away'], score['e']['away']))
        boxscore.append('| {:3} | {:>2} | {:>2} | {:>2} |'.format(game['home_name_abbrev'], score['r']['home'], score['h']['home'], score['e']['home']))
        boxscore.append('----------------------')

        if game['status']['status'] == 'Final':
            boxscore.append('W: {}'.format(self.get_deciding_pitcher_line(game['winning_pitcher']))) if 'winning_pitcher' in game else ''
            boxscore.append('L: {}'.format(self.get_deciding_pitcher_line(game['losing_pitcher']))) if 'losing_pitcher' in game else ''

            if 'save_pitcher' in game and game['save_pitcher']['name_display_roster'] != '':
                boxscore.append('S: {} ({})'.format(game['save_pitcher']['name_display_roster'], game['save_pitcher']['saves']))

        elif status == 'In Progress':
            runners = game['runners_on_base']
            boxscore.append('  {}    '.format("\u2b25" if 'runner_on_2b' in runners else "\u2b26"))
            boxscore[-1] += 'P:  {}'.format(game['pitcher']['name_display_roster'])

            boxscore.append('{}   '.format("\u2b25" if 'runner_on_3b' in runners else "\u2b26"))
            boxscore[-1] += '{}  AB: {}'.format("\u2b25" if 'runner_on_1b' in runners else "\u2b26", game['batter']['name_display_roster'])

            #boxscore.append(' {}-{} {} Out(s)'.format(game['status']['b'], game['status']['s'], game['status']['o']))
            boxscore.append('')

        return boxscore

    def print_detailed_boxscore(self, game):
        score = game['linescore']
        inning_count = max(9, len(score['inning']))
        
        header = [str(x) for x in range(1, inning_count + 1)] + ['r', 'h', 'e']
        away_runs = [x['away'] for x in score['inning']] + [score['r']['away'], score['h']['away'], score['e']['away']]
        home_runs = [x.get('home', ' ') for x in score['inning']] + [score['r']['home'], score['h']['home'], score['e']['home']]

        buf = []
        buf.append(game['time_date'])
        buf.append(game['location'] + ', ' + game['venue'])
        buf.append('--------------' + ('-----' * len(header)))
        buf.append(' {:11}'.format(game['status']['status']) + ' '.join(' {:>2} '.format(x) for x in header))
        buf.append('--------------' + ('-----' * len(header)))

        buf.append(' {:11}'.format(game['away_team_name']) + ' '.join(' {:>2} '.format(x) for x in away_runs))
        buf.append(' {:11}'.format(game['home_team_name']) + ' '.join(' {:>2} '.format(x) for x in home_runs))
        buf.append('--------------' + ('-----' * len(header)))
        buf.append('')

        return buf

def get_team_boxscore(game, sel):
    players = game['liveData']['boxscore']['teams'][sel]['players']
    batters = []
    for player in list(players.values()):
        if player['gameStats']['batting']['battingOrder'] != None:
            batters.append(player)

    batters.sort(key=lambda x: x['gameStats']['batting']['battingOrder'])

    lines = []
    lines.append(game['gameData']['teams'][sel]['name']['full'])
    for batter in batters:
        b_stat = batter['gameStats']['batting']
        lines.append('-' * 80)

        batter_template = ' {:14}' if int(b_stat['battingOrder']) % 100 == 0 else '   {:12}'
        template = batter_template + ' {:>10}' + ('  {:>2}' * 7) + ('  {:>5}' * 2)

        lines.append(template.format(
            batter['name']['boxname'], batter['position'], 
            b_stat['atBats'], b_stat['runs'], b_stat['hits'], b_stat['rbi'], b_stat['baseOnBalls'], b_stat['strikeOuts'], b_stat['leftOnBase'], 
            batter['seasonStats']['batting']['avg'], batter['seasonStats']['batting']['ops']
        ))
        
    lines.append('-' * 80)

    total = game['liveData']['boxscore']['teams'][sel]['battingTotals']
    lines.append((' {:14} {:>10}' + ('  {:>2}' * 7) + ('  {:>5}' * 2)).format(
        'Total', ' ' ,
        total['atBats'], total['runs'], total['hits'], total['rbi'], total['baseOnBalls'], total['strikeOuts'], total['leftOnBase'], '', ''
    ))

    lines.append('-' * 80)
    lines.append('')
    return lines

def print_boxscores(boxscores):
    terminal_size = shutil.get_terminal_size((80, 20))
    boxscore_columns = int(int(terminal_size.columns)/40)
    boxscore_rows = int(len(boxscores) / boxscore_columns)
    if len(boxscores) % boxscore_columns > 0:
        boxscore_rows += 1


    for i in range(0, boxscore_rows):
        for j in range(0, 9):
            for k in range(0, boxscore_columns):
                index = i * boxscore_columns + k
                if index >= len(boxscores):
                    print ('{:40}'.format(''), end='')
                elif j >= len(boxscores[index]):
                    print ('{:40}'.format(''), end='')
                else:
                    if j == 0:
                        print('{:40}'.format(str(i * boxscore_columns + k + 1) + '. ' + boxscores[index][j]), end='')
                    else:
                        print ('{:40}'.format(boxscores[index][j]), end='')

                if k == boxscore_columns - 1:
                    print ('')

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
    date = datetime.date.today()

    def print_rhe():
        scoreboard = ScoreboardManager.get_scoreboard(MlbShell.date)
        
        print('')
        print(scoreboard.date)
        print('')

        print_boxscores(scoreboard.get_boxscores())

    def do_box(self, arg):
        scoreboard = ScoreboardManager.get_scoreboard(MlbShell.date)
        scoreboard_game = scoreboard['game'][int(arg) - 1]
        game = json.loads(requests.get('http://statsapi.mlb.com/api/v1/game/' + scoreboard_game['game_pk']  + '/feed/live').text)
        boxscore = print_detailed_boxscore(scoreboard_game)
        print(*boxscore, sep='\n')

        team_boxscore = get_team_boxscore(game, 'away')
        print(*team_boxscore, sep='\n')
        team_boxscore = get_team_boxscore(game, 'home')
        print(*team_boxscore, sep='\n')

    def do_plays(self, arg):
        scoreboard = ScoreboardManager.get_scoreboard(MlbShell.date)
        scoreboard_game = scoreboard['game'][int(arg) - 1]
        game = json.loads(requests.get('http://statsapi.mlb.com/api/v1/game/' + scoreboard_game['game_pk']  + '/feed/live').text)

        scoring_indices = [int(x) for x in game['liveData']['plays']['scoringPlays']]
        scoring_plays = [game['liveData']['plays']['allPlays'][x] for x in scoring_indices]

        play_dict = {}
        for play in scoring_plays:
            key = play['about']['halfInning'].title() + ' ' + play['about']['inning']

            if key not in play_dict:
                play_dict[key] = []
                
            pitcher = game['liveData']['players']['allPlayers']['ID' + play['matchup']['pitcher']]
            play_dict[key].append(play['result']['description'] + pitcher['name']['first'] + ' ' + pitcher['name']['last'] + ' pitching.')

        for k,v in play_dict.items():
            print(k)
            for p in v:
                print('  ' + p)

            print('')


    def do_rhe(self, arg):
        MlbShell.print_rhe()

    def do_p(self, arg):
        MlbShell.date = MlbShell.date - datetime.timedelta(days=1)
        MlbShell.print_rhe()

    def do_n(self, arg):
        MlbShell.date = MlbShell.date + datetime.timedelta(days=1)
        MlbShell.print_rhe()

    def preloop(self):
       MlbShell.print_rhe()

    def do_quit(self, arg):
        return True
        
if __name__ == '__main__':
    MlbShell().cmdloop()


