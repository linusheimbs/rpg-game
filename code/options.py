import pygame

from settings import *
from config_manager import config_manager
from support import set_window_size


class Options:
    def __init__(self, bg_surf, fonts, funcs, main_menu=False):
        # display
        self.display_surface = pygame.display.get_surface()
        self.bg_surf = pygame.transform.scale(bg_surf, (config_manager.settings['video']['window_width'],
                                                        config_manager.settings['video']['window_height']))

        # fonts
        self.fonts = fonts

        # main menu
        self.main_menu = main_menu

        # functions to run
        self.funcs = funcs

        # selection
        self.selection_mode = 'general'
        self.ui_indexes = {
            'general': 0,
            'settings': 0,
            'audio': 0,
            'video': 0,
            'resolution': 0,
        }
        self.general_options = ['new game', 'save', 'load', 'settings', 'quit'] if self.main_menu\
            else ['resume', 'save', 'load', 'settings', 'main menu']
        self.setting_options = ['audio', 'video']
        self.audio_options = ['all']
        self.video_options = ['windowed', 'fullscreen']
        self.resolution_options = ['1280 x 720', '1600 x 900', '1920 x 1000']

    def draw_ui(self):
        if self.selection_mode == 'general':
            self.draw_selection('general', self.general_options)
        elif self.selection_mode == 'settings':
            self.draw_selection('settings', self.setting_options)
        elif self.selection_mode == 'audio':
            self.draw_selection('audio', self.audio_options)
        elif self.selection_mode == 'video':
            self.draw_selection('video', self.video_options)
        elif self.selection_mode == 'resolution':
            self.draw_selection('resolution', self.resolution_options)

    def draw_selection(self, selection_type, selection_menu):
        width, height = config_manager.settings['video']['window_width']*0.4,\
                        config_manager.settings['video']['window_height']*0.8
        bg_rect = pygame.FRect(config_manager.settings['video']['window_width']*0.3,
                               config_manager.settings['video']['window_height']*0.1, width, height)
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        item_height = bg_rect.height/len(selection_menu)

        for index, value in enumerate(selection_menu):
            selected = index == self.ui_indexes[selection_type]
            # text
            if selected:
                text_color = COLORS['light']
            else:
                text_color = COLORS['dark']
            text_surf = self.fonts['bold'].render(value, False, text_color)
            # rect
            text_rect = text_surf.get_frect(center=bg_rect.midtop + vector(0, item_height/2 + index * item_height))
            text_bg_rect = pygame.FRect((0, 0), (width, item_height)).move_to(center=text_rect.center)
            # draw
            if bg_rect.collidepoint(text_rect.center):
                if selected:
                    if text_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, 0, 0, 5, 5)
                    elif text_bg_rect.collidepoint(bg_rect.midbottom + vector(0, -1)):
                        pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, 0, 0, 0, 0, 5, 5)
                    else:
                        pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect)
                self.display_surface.blit(text_surf, text_rect)

    def draw_slider(self):
        print(self.reset)

    def input(self):
        keys = pygame.key.get_just_pressed()

        # limit selection
        match self.selection_mode:
            case 'general':
                limiter = len(self.general_options)
            case 'settings':
                limiter = len(self.setting_options)
            case 'audio':
                limiter = len(self.audio_options)
            case 'resolution':
                limiter = len(self.resolution_options)
            case 'video':
                limiter = len(self.video_options)
            case _:
                limiter = 1

        # movement
        if limiter > 0:
            if keys[pygame.K_w]:
                self.ui_indexes[self.selection_mode] = (self.ui_indexes[self.selection_mode] - 1) % limiter
            elif keys[pygame.K_s]:
                self.ui_indexes[self.selection_mode] = (self.ui_indexes[self.selection_mode] + 1) % limiter

        if keys[pygame.K_SPACE] or keys[pygame.K_f]:
            if self.selection_mode == 'general':
                if self.ui_indexes[self.selection_mode] == 0:
                    if self.main_menu:
                        self.funcs['new_game']()
                    self.running = False
                elif self.ui_indexes[self.selection_mode] == 3:
                    self.selection_mode = 'settings'
                elif self.ui_indexes[self.selection_mode] == 4:
                    if self.main_menu:
                        pygame.quit()
                        exit()
                    else:
                        self.funcs['open_main_menu']()
                        self.funcs['close_game']()
                        self.running = False
            elif self.selection_mode == 'settings':
                if self.ui_indexes[self.selection_mode] == 0:
                    self.selection_mode = 'audio'
                elif self.ui_indexes[self.selection_mode] == 1:
                    self.selection_mode = 'video'
            elif self.selection_mode == 'video':
                if self.ui_indexes[self.selection_mode] == 0:
                    self.selection_mode = 'resolution'
                elif self.ui_indexes[self.selection_mode] == 1:
                    if pygame.display.is_fullscreen() is False:
                        set_window_size(1920, 1080)
                        config_manager.update_setting('video', 'fullscreen', True)
                        pygame.display.toggle_fullscreen()
                        self.adjust_surface()
            elif self.selection_mode == 'resolution':
                if not int(self.display_surface.get_width())\
                       == int(self.resolution_options[self.ui_indexes[self.selection_mode]].split(' ')[0]):
                    if pygame.display.is_fullscreen() is True:
                        pygame.display.toggle_fullscreen()
                        config_manager.update_setting('video', 'fullscreen', False)
                    set_window_size(
                        *map(int, self.resolution_options[self.ui_indexes[self.selection_mode]].split(' x ')))
                    self.adjust_surface()
            elif self.selection_mode == 'audio':
                if self.ui_indexes[self.selection_mode] == 0:
                    config_manager.update_setting('audio', 'all', 0.2)

        if keys[pygame.K_ESCAPE]:
            if self.selection_mode == 'general':
                self.running = False
            elif self.selection_mode == 'settings':
                self.selection_mode = 'general'
                self.reset()
            elif any([self.selection_mode == 'audio', self.selection_mode == 'video']):
                self.selection_mode = 'settings'
                self.reset()
            elif self.selection_mode == 'resolution':
                self.selection_mode = 'video'
                self.reset()

    def reset(self):
        self.ui_indexes = {k: 0 for k in self.ui_indexes}

    def adjust_surface(self):
        self.bg_surf = pygame.transform.scale(self.bg_surf, (config_manager.settings['video']['window_width'],
                                                             config_manager.settings['video']['window_height']))
        if 'adjust_surfaces' in self.funcs:
            self.funcs['adjust_surfaces']()

    def run(self):

        self.running = True

        while self.running:
            self.display_surface.fill(COLORS['black'])
            # event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # input
            self.input()

            # drawing
            self.display_surface.blit(self.bg_surf, (0, 0))
            self.draw_ui()

            pygame.display.update()
