import pygame

from settings import *
from config_manager import config_manager
from options import Options
from support import *
from game import Game


class MainMenu:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode(
            (config_manager.settings['video']['window_width'], config_manager.settings['video']['window_height']),
            flags=pygame.FULLSCREEN if config_manager.settings['video']['fullscreen'] is True else 0)
        pygame.display.set_caption('rpg-game')
        self.bg_frames = import_folder_dict('..', 'graphics', 'backgrounds')
        self.option_functions = {
            'new_game': self.load_game,
            'load': self.load_game
        }
        self.options = Options(self.bg_frames['forest'], self.option_functions, True)
        self.game = None
        self.open = True

    def load_game(self, filename=None):
        self.open = not self.open
        if not self.open:
            self.game = Game(self.load_game)
            if filename:
                self.game.load_game(filename)

    def run(self):
        while True:
            if self.open:
                self.game = None
                self.options.run()
            else:
                self.game.run()

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()


if __name__ == '__main__':
    main_menu = MainMenu()
    main_menu.run()
