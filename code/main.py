from settings import *
from options import Options
from support import *
from game import Game


class MainMenu:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode(
            (settings['window']['window_width'], settings['window']['window_height']))
        pygame.display.set_caption('rpg-game')
        self.fonts = {
            'bold': pygame.font.Font(join('..', 'graphics', 'fonts', 'dogicapixelbold.otf'), 30)
        }
        self.bg_frames = import_folder_dict('..', 'graphics', 'backgrounds')
        self.option_functions = {
            'new_game': self.change_state
        }
        self.options = Options(self.bg_frames['forest'], self.fonts, self.option_functions, True)
        self.game = None
        self.open = True

    def change_state(self):
        self.open = not self.open
        if not self.open:
            self.game = Game(self.change_state)

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
