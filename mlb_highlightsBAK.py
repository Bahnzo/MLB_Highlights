import requests
import json
import bs4


class GameData():
    """
    Holds data for each game played on a certain day
    """
    game_pk = ''  # unique id for each game
    id = ''  # game id in format "2015/06/18/texmlb-lanmlb-1"
    away_team_name = ''
    home_team_name = ''
    event_time = ''  # start time EST
    free = ''  # is this the "Free game of the day on MLB.TV?
    calendar_event_id = ''  # another unique id for the game
    media_state = ''  # game over?


class ReplayData():
    """
    Holds data for each replay generated
    """
    game_pk = ''  # unique id for each game
    id = ''  # unique id for each replay (larger = later in game?)
    headline = ''  # headline for replay
    replay_url = ''  # full url for replay


def build_menu(games):
    """
    Builds a menu of available games
    :param games: list of GameData() objects
    :return: dict with k,v - game name (away_team @ home_team), game_pk
    """
    game_dict = {}
    for game in games:
        title = '{} @ {}'.format(game.away_team_name, game.home_team_name)
        game_pk = game.game_pk
        game_dict[title] = game_pk
    return game_dict


def build_game_data(name):
    """
    Builds information about the days games. creates a GameData object to store the data
    :param name: str
    :return: GameData() object
    """
    name = GameData()
    name.game_pk = game['game_pk']
    name.id = game['id']
    name.away_team_name = game['away_team_name']
    name.home_team_name = game['home_team_name']
    name.event_time = game['event_time']
    try: name.free = game['game_media']['homebase']['media'][0]['free']
    except: name.free = 'NO'
    name.calendar_event_id = game['calendar_event_id']
    name.media_state = game['media_state']

    return name


def find_free_game(games):
    """
    finds the Free Game of the Day on MLB.TV
    :param games: list of GameData() objects
    :return: the free game's unique id: game_pk
    """
    for game in games:
        if game.free == 'ALL':
            return game.game_pk


def build_game_highlights(data):
    """
    builds video highlights for each game
    :param data: XML data
    :return: list of ReplayData() objects
    """
    game_highlights = []
    video = data.find_all('media', type='video')
    for tag in video:
        pk = data.attrs['game_pk']
        pk = ReplayData()
        pk.game_pk = data.attrs['game_pk']
        pk.id = tag.attrs['id']
        pk.headline = tag.contents[1].text
        pk.replay_url = tag.contents[11].text
        game_highlights.append(pk)
    return game_highlights


url = 'http://gd2.mlb.com/components/game/mlb/year_2015/month_06/day_18/grid.json'
media_url = 'http://gd2.mlb.com/components/game/mlb/year_2015/month_06/day_18/media/highlights.xml'
days_games = []  # holds GameData() objects with data for each game.
replay_data = []  # holds ReplayData() objects with data for each replay

response = requests.get(url)
response.raise_for_status()
replay = json.loads(response.text)

games = replay['data']['games']['game']
for game in games:  # build game data
    name = game['home_name_abbrev']
    days_games.append(build_game_data(name))

response = requests.get(media_url)
response.raise_for_status()
page = bs4.BeautifulSoup(response.text, 'lxml')

free_game = find_free_game(days_games)
menu_dict = build_menu(days_games)
highlights = page.find_all('highlights')

for game in days_games:  # builds replay data for all games with highlights
    for data in highlights:
        if game.game_pk not in data.attrs['game_pk']:  # some games don'y have highlights, deal with that eventually
            continue
        else:
            replay_data.append(build_game_highlights(data))



print('done')
