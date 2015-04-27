__author__ = 'Harry'
import pygame
import events
from random import randint
import json
import sqlite3 as lite

db = lite.connect('login.db')
query = db.cursor()

def login_check(username, password):
    """return 0 if username is in database/pass incorrect, 1 if info correct, 2 is username not in db"""
    #with is like a fancy 'try+catch' for db
    with db:
        query.execute("CREATE TABLE IF NOT EXISTS Users(username TEXT, password TEXT, h_score INT)")
        #check if username exists in db
        query.execute("SELECT * FROM Users WHERE username = ?", (username, ))
        check=query.fetchone()

        #if username does not exist, add to users table in db
        if check is None:
            print("Username does not exist")
            return 2
            #code below inserts the new user into db
            query.execute("INSERT INTO Users VALUES(?, ?, ?)", (username, password, 0))
        else:
            #if username exists, check if pass correct
            query.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password, ))
            check=query.fetchone()

            #if wrong password
            if check is None:
                print("Wrong password")
                return 0
            #else success
            else:
                return 1


def update_hscore(USERNAME, H_SCORE):
    with db:
        query.execute("UPDATE Users SET h_score = ? WHERE username = ?", (H_SCORE, USERNAME))

def get_hscore(USERNAME):
    with db:
        query.execute("SELECT h_score FROM Users WHERE username = ?", (USERNAME, ))
        score = query.fetchone()
        return score

class Score:

    def __init__(self, high_score_file):
        self._high_score_file = high_score_file
        self._current_score = 0
        self._high_score = 0
        self._high_score_changed = False
        try:
            high_score_file = open(self._high_score_file, "r")
            self._high_score = int(high_score_file.read())
            high_score_file.close()
        except IOError:
            print("No high score found, Starting at 0")
        except ValueError:
            print("High score file is not an int, starting at 0")

    def save_high_score(self):
        if self._high_score_changed:
            try:
                high_score_file = open(self._high_score_file, "w")
                high_score_file.write(str(self._high_score))
                high_score_file.close()
                self._high_score = self._current_score
                print("High score saved.")
            except IOError:
                print("Unable to save high score.")

    def get_high_score(self):
        return self._high_score

    def get_current_score(self):
        return self._current_score

    def get_scores(self):
        return [self._current_score, self._high_score]

    def increment_current_score(self):
        self._current_score += 1
        if self._current_score > self._high_score:
            self._high_score = self._current_score
            self._high_score_changed = True

    def reset_score(self):
        self._current_score = 0
        self._high_score_changed = False


class Snake:
    def __init__(self, x, y, direction, event_listener):
        self._direction = direction
        self._head = pygame.Rect(x, y, 15, 15)
        self._parts = []
        if direction == "right":
            self._parts.append(pygame.Rect(x - 15, y, 15, 15))
        if direction == "left":
            self._parts.append(pygame.Rect(x + 15, y, 15, 15))
        if direction == "up":
            self._parts.append(pygame.Rect(x, y + 15, 15, 15))
        if direction == "down":
            self._parts.append(pygame.Rect(x, y - 15, 15, 15))
        self._event_listener = event_listener

    def detect_collision(self):
        return self._head.collidelist(self._parts)

    def detect_border(self, borders):
        return self._head.collidelist(borders)

    def get_head(self):
        return self._head

    def get_parts(self):
        return self._parts

    def get_head_and_parts_coordinates(self):
        result = [[self._head.left, self._head.top]]
        for part in self._parts:
            result.append([part.left, part.top])
        return result

    def add_part(self):
        if len(self._parts) == 1:
            first_part = self._head
        else:
            first_part = self._parts[len(self._parts) - 2]
        second_part = self._parts[len(self._parts) - 1]
        if first_part.left - second_part.left == 15:
            self._parts.append(pygame.Rect(second_part.left - 15, second_part.top, 15, 15))
        elif first_part.left - second_part.left == -15:
            self._parts.append(pygame.Rect(second_part.left + 15, second_part.top, 15, 15))
        elif first_part.top - second_part.top == 15:
            self._parts.append(pygame.Rect(second_part.left, second_part.top - 15, 15, 15))
        elif first_part.top - second_part.top == -15:
            self._parts.append(pygame.Rect(second_part.left, second_part.top + 15, 15, 15))

    def update(self, direction):
        for i in range(len(self._parts) - 1, -1, -1):
            self._parts[i].left = self._parts[i - 1].left
            self._parts[i].top = self._parts[i - 1].top

        self._parts[0].left = self._head.left
        self._parts[0].top = self._head.top

        if direction != "":
            if not (self._direction == "left" and direction == "right" or self._direction == "right" and direction == "left" or self._direction == "up" and direction == "down" or self._direction == "down" and direction == "up"):
                self._direction = direction

        if self._direction == "right":
            self._head.left += 15
        elif self._direction == "left":
            self._head.left -= 15
        elif self._direction == "up":
            self._head.top -= 15
        elif self._direction == "down":
            self._head.top += 15


class Game:
    def __init__(self, event_manager):
        self._event_manager = event_manager
        self._event_manager.register_listener(self)
        self._clock = pygame.time.Clock()
        self._snakes = []
        self._snakes.append(Snake(400, 300, "down", self._event_manager))
        self._pellets = []
        self._pellets.append(pygame.Rect(randint(2, 53) * 15, randint(2, 39) * 15, 15, 15))
        self._borders = [pygame.Rect(0, 0, 2, 600), pygame.Rect(0, 0, 800, 2), pygame.Rect(798, 0, 2, 600), pygame.Rect(0, 598, 800, 2)]
        self._score = Score("high_score.txt")
        self._is_running = True
        self._game_state = "run"

    def run(self):
        while self._is_running:
            self._clock.tick(10)
            if self._game_state == "run":
                for snake in self._snakes:
                    snake.update("")
                    if snake.detect_border(self._borders) != -1 or snake.detect_collision() != -1:
                        self._event_manager.post(events.GameOverEvent())
                    for pellet in self._pellets:
                        if snake.get_head().colliderect(pellet):
                            snake.add_part()
                            self._pellets.clear()
                            self._pellets.append(pygame.Rect(randint(2, 53) * 15, randint(2, 39) * 15, 15, 15))
                            self._score.increment_current_score()
            self._event_manager.post(events.TickEvent())

    def notify(self, event):
        if isinstance(event, events.QuitEvent):
            self._is_running = False
        elif isinstance(event, events.GameOverEvent):
            self._score.save_high_score()
            self._game_state = "game over"
        elif isinstance(event, events.MoveEvent):
            self._snakes[0].update(event.get_direction())
        elif isinstance(event, events.RestartEvent):
            self._snakes.clear()
            self._snakes.append(Snake(400, 300, "down", self._event_manager))
            self._score.reset_score()
            self._game_state = "run"
        elif isinstance(event, events.LoginAttempt):
            enum = login_check(event.get_username(), event.get_password())
            if enum == 0:
                self._event_manager.post(events.LoginFail())
            elif enum == 1:
                self._event_manager.post(events.LoginSuccess())
            elif enum == 2:
                self._event_manager.post(events.UserCreated())

    def get_snakes(self):
        return self._snakes

    def get_pellets(self):
        return self._pellets

    def get_pellet_coordinates(self):
        result = []
        for pellet in self._pellets:
            result.append([pellet.left, pellet.top])
        return result

    def get_score(self):
        return self._score.get_current_score(), self._score.get_high_score()

    def get_game_state(self):
        return self._game_state

    def receive_message(self, message):
        loaded_json = json.loads(message)
        print(json.dumps(loaded_json, sort_keys=True, indent=4))

    def send_update(self):
        json_string = json.dumps(dict([("snakes", self._snakes[0].get_head_and_parts_coordinates()),
                                       ("pellets", self.get_pellet_coordinates()),
                                       ("scores", self._score.get_scores()),
                                       ("game_state", self._game_state)]))
        return json_string