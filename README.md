# batterm
A console app to get MLB linescores, box scores, and more.

## Installation
Clone the repository and run the following command:
```bash
pip install --user -r requirements.txt
```

After pip finishes, run batterm with:
```bash
python batterm/batterm.py
```

batterm currently only works with python 3+

## Usage

### rhe command
Get simplied RHE boxscores for the given day

```bash
(batterm) rhe           # today's scores
(batterm) rhe 9         # the ninth of this month's scores
(batterm) rhe 5-9       # May 9 of this year's scores
(batterm) rhe 2016-5-9  # May 9, 2016 scores
```

![alt text](http://imgur.com/RxlEjZd.png)

### p & n commands
Get the previous and next RHE boxscores
```bash
(batterm) p   # the previous day's RHE scores
(batterm) n   # the next day's RHE scores
```

### box command
Get detailed boxscore of a particular game
```bash
(batterm) box 5  # the 5 specified the 3rd RHE game
```

![alt text](http://imgur.com/g811waN.png)

### plays command
Get run scoring plays of a particular game
```bash
(batterm) plays 3  # the 3 specified the 3rd RHE game 
```

![alt text](http://imgur.com/6AR7MKr.png)

## Upcoming features
* Standings command for division and wild card standings
* Split column view for detailed box scores for larger terminal sizes
* More data in detailed boxscore like pitching stats
* More!
