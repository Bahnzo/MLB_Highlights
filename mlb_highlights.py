import requests
import json
import bs4
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtMultimedia import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap
import mlbui
import sys
import videowidget
import re


class MainWindow(QMainWindow, mlbui.Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.single_game_highlights_ordered = []
        self.single_game_highlights = {}
        date = QDate.currentDate()
        self.dateEdit.setDate(date)  # sets the dateEdit window to the current date
        self.set_team_logos()
        self.listWidget.itemDoubleClicked.connect(self.display_single_game_replays)  # team double clicked
        self.replay_window.itemDoubleClicked.connect(self.replay_clicked)  # replay double clicked
        self.get_game_button.clicked.connect(self.game_button_clicked)  # gets date


    def set_team_logos(self):
        self.team_logos = {'Angels': 'ana.jpg', 'D-backs': 'ari.jpg', 'Braves': 'atl.jpg',
                          'Orioles': 'bal.jpg', 'Red Sox': 'bos.jpg', 'Cubs': 'chc.jpg', 'Reds': 'cin.jpg',
                          'Indians': 'cle.jpg', 'Rockies': 'col.jpg', 'White Sox': 'cws.jpg', 'Tigers': 'det.jpg',
                          'Astros': 'hou.jpg', 'Royals': 'kc.jpg', 'Dodgers': 'la.jpg', 'Marlins': 'mia.jpg',
                          'Brewers': 'mil.jpg', 'Twins': 'min.jpg', 'Mets': 'nym.jpg', 'Yankees': 'nyy.jpg',
                          'A\'s': 'oak.jpg', 'Phillies': 'phi.jpg', 'Pirates': 'pit.jpg', 'Padres': 'sd.jpg',
                          'Mariners': 'sea.jpg', 'Giants': 'sf.jpg', 'Cardinals': 'stl.jpg', 'Rays': 'tb.jpg',
                          'Rangers': 'tex.jpg', 'Blue Jays': 'tor.jpg', 'Nationals': 'was.jpg'}

    def game_button_clicked(self):
        """
        gets the date and goes to the MLB site and gets the games from that date
        :return:
        """
        self.listWidget.clear()
        item = self.dateEdit.date().toPyDate()  # returns date in format "mm-dd-yyyy"
        date_of_games = str(item).split('-')  # splits date up into a list
        year = date_of_games[0]
        month = date_of_games[1]
        day = date_of_games[2]
        self.day_url = 'http://gd2.mlb.com/components/game/mlb/year_{}/month_{}/day_{}/grid.json'.format(year, month, day)
        self.media_url = 'http://gd2.mlb.com/components/game/mlb/year_{}/month_{}/day_{}/media/highlights.xml'.format(year, month, day)
        self.games_of_the_day = self.get_date_json()  # gets the games for the chosen date
        self.menu_dict = self.build_menu(self.games_of_the_day)  # builds a dict of the games and their unique id
        free_game = self.find_free_game(self.games_of_the_day)  # finds the MLB free game of the day
        self.free_game_label.setText(free_game)  # set's the label for the window of the free game
        self.replay_data = self.get_highlight_xml(self.games_of_the_day)  # gets the replay data for all the games

    def replay_clicked(self):
        """
        gets the replay the user clicks on, and then sends it's to the video object to play
        :return:
        """
        if self.radioButton.isChecked():
            self.play_all_replays()
        else:
            replay = self.replay_window.currentItem().text()  # name of the replay
            for k, v in self.single_game_highlights.items():
                if k == replay:
                    url = v
                    break
            self.dialog = videowidget.VideoPlayer()  # the videowidget object of the imported file
            self.dialog.mediaPlayer.setMedia(QMediaContent(QUrl(url)))  # sets the file to play
            self.dialog.mediaPlayer.play()
            self.dialog.setWindowTitle('MLB Replay')
            self.dialog.show()

        #item = self.replay_window.currentItem().text()
        #QMessageBox.warning(self, 'Warning!', '%s' % item)

    def play_all_replays(self):
        """
        creates a QMediaPlaylist object and inserts all the games replays (in order) to the playlist
        and then plays it.
        :return:
        """
        self.dialog = videowidget.VideoPlayer()
        self.playlist = QMediaPlaylist()
        self.dialog.mediaPlayer.setPlaylist(self.playlist)
        for v in self.single_game_highlights_ordered:
            url = QUrl(v)
            self.playlist.addMedia(QMediaContent(url))
        self.dialog.mediaPlayer.setPlaylist(self.playlist)

        self.playlist.setCurrentIndex(0)
        self.dialog.mediaPlayer.play()
        self.dialog.setWindowTitle('MLB Replay')
        self.dialog.show()

    def display_single_game_replays(self):
        """
        builds and displays the selected game's highlights
        :param menu_dict: games of the day with unique id
        :param replay_data: xml of the replay info
        :return: ??
        """
        found = False
        self.replay_window.clear()
        teams = self.listWidget.currentItem().text()
        for game, key in self.menu_dict.items():
            if teams == game:
                game_id = key
                for games in self.replay_data:
                    if games[0].game_pk == game_id:  # find the game
                        found = True
                        for replay in games:
                            self.replay_window.addItem('{}'.format(replay.headline))  # adds Title to window
                            self.single_game_highlights_ordered.append(replay.replay_url)
                            self.single_game_highlights[replay.headline] = replay.replay_url  # creates dict entry
                        break
        if not found:
            QMessageBox.warning(self, 'Warning!', 'No replay data found for this game')

    def show_game(self):
        """
        shows the games in the listWidget
        :return:
        """
        item = self.listWidget.currentItem().text()
        self.lineEdit.setText(item)

    def build_menu(self, games):
        """
        Builds a menu of available games
        :param games: list of GameData() objects
        :return: dict with k,v - game name (away_team @ home_team), game_pk
        """
        game_dict = {}
        for game in games:
            title = '{} @ {}'.format(game.away_team_name, game.home_team_name)
            self.listWidget.addItem(title)
            game_pk = game.game_pk
            game_dict[title] = game_pk
        return game_dict

    def build_game_data(self, name, game):
        """
        Builds information about the days games. creates a GameData object to store the data
        :param game: str
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

    def find_free_game(self, games):
        """
        finds the Free Game of the Day on MLB.TV
        :param games: list of GameData() objects
        :return: str of the free game
        """
        away_label = self.away_team_label
        home_label = self.home_team_label
        for game in games:
            if game.free == 'ALL':
                home_pixmap = QPixmap('./logos/' + self.team_logos[game.home_team_name])
                away_pixmap = QPixmap('./logos/' + self.team_logos[game.away_team_name])
                away_label.setPixmap(away_pixmap)
                home_label.setPixmap(home_pixmap)
                return '{} @ {}'.format(game.away_team_name, game.home_team_name)

    def build_game_highlights(self, data):
        """
        builds video highlights for each game
        :param data: XML data
        :return: list of ReplayData() objects
        """
        game_highlights = []
        video = data.find_all('media', type='video')
        media = re.compile(r'(http://.*\.mp4)')
        for tag in video:
            pk = data.attrs['game_pk']
            pk = ReplayData()
            pk.game_pk = data.attrs['game_pk']
            pk.id = tag.attrs['id']
            text = tag.text.strip().split('\n')
            pk.headline = text[0]
            pk.length = text[1]
            mo = media.search(tag.text)
            pk.replay_url = mo.group()
            game_highlights.append(pk)
        game_highlights.sort(key=lambda x: x.id)  # sorts the list based on the game id
        return game_highlights

    def get_date_json(self):
        """
        loads the date selected and builds a list of the games that day
        :return: list of game objects
        """
        url = self.day_url
        days_games = []  # holds GameData() objects with data for each game.
        response = requests.get(url)
        response.raise_for_status()
        replay = json.loads(response.text)
        games = replay['data']['games']['game']
        for game in games:  # build game data
            name = game['home_name_abbrev']
            days_games.append(self.build_game_data(name, game))
        return days_games

    def get_highlight_xml(self, days_games):
        """
        Gets the highlights in XML form from MLB and returns a list of objects containing
        each games highlists
        :param days_games:
        :return: list of objects with the highlight data
        """
        replay_data = []  # holds ReplayData() objects with data for each replay
        response = requests.get(self.media_url)
        if response.status_code == 404:
            QMessageBox.warning(self, 'Warning!', '404 - Not Found Error\nNo Media found for this date.')
        else:
            response.raise_for_status()
            page = bs4.BeautifulSoup(response.text, 'lxml')
            highlights = page.find_all('highlights')
            for game in days_games:  # builds replay data for all games with highlights
                for data in highlights:
                    if game.game_pk not in data.attrs['game_pk']:  # some games don'y have highlights, deal with that eventually
                        pass
                    else:
                        replay_data.append(self.build_game_highlights(data))
        return replay_data


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
    length = ''  # length of the replay
    headline = ''  # headline for replay
    replay_url = ''  # full url for replay


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    #app.exec_()

if __name__ == '__main__':
    main()


# TODO: impliment next and prev buttons. Probably in the videowidget.py file