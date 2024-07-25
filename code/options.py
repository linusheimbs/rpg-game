import os.path
import sys
from tkinter import Tk as tk

import pygame

from debug import debug
from settings import *
from os.path import join
from config_manager import config_manager
from support import set_window_size


class Options:
    # main
    def __init__(self, bg_surf, funcs, main_menu=False):
        # display
        self.display_surface = pygame.display.get_surface()
        self.bg_surf = pygame.transform.scale(bg_surf, (config_manager.settings['video']['window_width'],
                                                        config_manager.settings['video']['window_height']))

        # fonts
        screen_width, _ = self.display_surface.get_size()
        font_size_ratio = 0.015
        font_size = int(screen_width * font_size_ratio)
        self.fonts = {
            'bold': pygame.font.Font(join('..', 'graphics', 'fonts', 'dogicapixelbold.otf'), font_size)
        }

        # main menu
        self.main_menu = main_menu

        # functions to run
        self.funcs = funcs

        # selection
        self.ui_indexes = {
            'general': 0,
            'settings': 0,
            'audio': 0,
            'video': 0,
            'resolution': 0,
            'controls': 0,
            'controls2': 0,
            'control_selection': 0,
            'save': 0,
            'load': 0
        }
        self.selection_mode = 'general'
        self.selected_control = None

        # options
        self.general_options = ['new game', 'save', 'load', 'settings', 'quit'] if self.main_menu \
            else ['resume', 'save', 'load', 'settings', 'main menu']
        self.setting_options = ['audio', 'video', 'controls']
        self.audio_options = ['music', 'sfx']
        self.video_options = ['windowed', 'fullscreen']
        self.resolution_options = ['1280 x 720', '1600 x 900', '1920 x 1080']
        self.controls_options = [
            {'action': 'up', 'keys': ['up', 'up']},
            {'action': 'down', 'keys': ['down', 'down']},
            {'action': 'left', 'keys': ['left', 'left']},
            {'action': 'right', 'keys': ['right', 'right']},
            {'action': 'confirm', 'keys': ['confirm', 'confirm']},
            {'action': 'inventory', 'keys': ['inventory', 'inventory']}
        ]
        self.not_usable_keys = [pygame.K_ESCAPE]
        self.used_keys = list(key for key_pair in config_manager.settings['controls'].values() for key in key_pair)
        self.save_options = [f'Save Slot {i}' for i in range(10)]
        self.load_options = ['Quick Load'] + [f'Load Slot {i}' for i in range(10)]

        # controls
        self.action_of_new_key = None
        self.new_key = None

    # drawing
    def draw_ui(self):
        if self.selection_mode == 'general':
            self.draw_general_menu('general', self.general_options)
        elif self.selection_mode == 'settings':
            self.draw_general_menu('settings', self.setting_options)
        elif self.selection_mode == 'audio':
            self.draw_general_menu('audio', self.audio_options)
            self.draw_slider('audio', self.audio_options)
        elif self.selection_mode == 'video':
            self.draw_general_menu('video', self.video_options)
        elif self.selection_mode == 'resolution':
            self.draw_general_menu('resolution', self.resolution_options)
        elif self.selection_mode == 'controls':
            self.draw_controls_menu()
        elif self.selection_mode == 'control_selection':
            self.draw_controls_menu(self.controls_options[self.ui_indexes['controls']]['action'], self.new_key)
        elif self.selection_mode == 'save':
            self.draw_save_menu()
        elif self.selection_mode == 'load':
            self.draw_load_menu()

    def draw_general_menu(self, selection_type, selection_menu):
        width, height = config_manager.settings['video']['window_width'] * 0.4, \
                        config_manager.settings['video']['window_height'] * 0.8
        bg_rect = pygame.FRect(config_manager.settings['video']['window_width'] * 0.3,
                               config_manager.settings['video']['window_height'] * 0.1, width, height)
        pygame.draw.rect(self.display_surface, COLORS['light-gray'], bg_rect, 0, 12)

        item_height = bg_rect.height / len(selection_menu)

        for index, value in enumerate(selection_menu):
            selected = index == self.ui_indexes[selection_type]

            # Text rendering
            text_color = COLORS['dark'] if selected else COLORS['light']
            text_surf = self.fonts['bold'].render(value, True, text_color)

            # Text rectangle
            text_rect = text_surf.get_rect(
                center=bg_rect.midtop + pygame.math.Vector2(0, item_height / 2 + index * item_height))
            text_bg_rect = pygame.Rect(0, 0, width, item_height)
            text_bg_rect.center = text_rect.center

            # Draw item background with rounded corners
            if selected:
                pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, border_radius=12)
                pygame.draw.rect(self.display_surface, COLORS['light'], text_bg_rect.inflate(-6, -6),
                                 border_radius=12)

            # Shadow effect
            shadow_offset = (2, 2)
            shadow_color = COLORS['black']
            shadow_rect = text_rect.move(*shadow_offset)
            shadow_surf = self.fonts['bold'].render(value, True, shadow_color)
            self.display_surface.blit(shadow_surf, shadow_rect)

            # Blit the text surface
            self.display_surface.blit(text_surf, text_rect)

    def draw_slider(self, selection_type, selection_menu):
        width = config_manager.settings['video']['window_width'] * 0.4
        height = config_manager.settings['video']['window_height'] * 0.8
        bg_rect = pygame.FRect(config_manager.settings['video']['window_width'] * 0.3,
                               config_manager.settings['video']['window_height'] * 0.1, width, height)
        item_height = bg_rect.height / len(selection_menu)

        slider_width = width * 0.8
        slider_height = 20
        slider_y_offset = config_manager.settings['video']['window_height'] * 0.05  # Space between text and slider

        for index, value in enumerate(selection_menu):
            selected = index == self.ui_indexes[selection_type]
            slider_x = bg_rect.centerx - slider_width / 2
            slider_y = bg_rect.midtop[1] + (item_height / 2 + index * item_height) + slider_y_offset

            # Draw slider bar
            slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
            pygame.draw.rect(self.display_surface, COLORS['dark white' if selected else 'white'], slider_rect)

            # Draw slider thumb
            slider_value = config_manager.settings[self.selection_mode][value]
            thumb_x = slider_x + slider_value * slider_width
            thumb_rect = pygame.Rect(thumb_x - 10, slider_y - 5, 20, slider_height + 10)
            pygame.draw.rect(self.display_surface, COLORS['black' if selected else 'gray'], thumb_rect)

            # Render slider value text
            slider_value_text = self.fonts['bold'].render(
                f"{slider_value: .2f}", True, COLORS['dark' if selected else 'light'])
            text_x = slider_x + slider_width / 2 - slider_value_text.get_width() / 2
            text_y = slider_y + slider_y_offset
            slider_value_text_rect = slider_value_text.get_rect().move((text_x, text_y))

            # Shadow effect
            shadow_offset = (2, 2)
            shadow_color = COLORS['black']
            shadow_rect = slider_value_text_rect.move(shadow_offset)
            shadow_surf = self.fonts['bold'].render(f"{slider_value: .2f}", True, shadow_color)
            self.display_surface.blit(shadow_surf, shadow_rect)

            # Blit value of slider
            self.display_surface.blit(slider_value_text, slider_value_text_rect)

    def draw_controls_menu(self, selected_key=None, new_key=None):
        width, height = config_manager.settings['video']['window_width'] * 0.4, \
                        config_manager.settings['video']['window_height'] * 0.8
        bg_rect = pygame.FRect(config_manager.settings['video']['window_width'] * 0.3,
                               config_manager.settings['video']['window_height'] * 0.1, width, height)

        action_bg_rect = pygame.FRect(bg_rect.left, bg_rect.top, width / 3, bg_rect.height)
        keys_bg_rect = pygame.FRect(bg_rect.left + width / 3, bg_rect.top, 2 * width / 3, bg_rect.height)

        pygame.draw.rect(self.display_surface, COLORS['light-gray'], action_bg_rect, 0, 0, 12, 0, 12)
        pygame.draw.rect(self.display_surface, COLORS['light-gray'], keys_bg_rect, 0, 0, 0, 12, 0, 12)

        item_height = round(bg_rect.height / len(self.controls_options), 2)

        # Shadow effect
        shadow_offset = (2, 2)
        shadow_color = COLORS['black']

        for index, control in enumerate(self.controls_options):
            action_text_surf = self.fonts['bold'].render(control['action'], False, COLORS['light'])
            action_text_rect = action_text_surf.get_rect(
                center=action_bg_rect.midtop + vector(0, item_height / 2) + vector(0, index * item_height))

            # Shadow effect
            shadow_rect = action_text_rect.move(shadow_offset)
            shadow_surf = self.fonts['bold'].render(control['action'], True, shadow_color)
            self.display_surface.blit(shadow_surf, shadow_rect)

            self.display_surface.blit(action_text_surf, action_text_rect)

            selected_vertical = self.ui_indexes['controls']
            selected_horizontal = self.ui_indexes['controls2']

            for i, key_name in enumerate(control['keys']):
                if index == selected_vertical:
                    double_keys = config_manager.settings['controls'][key_name]
                    key_code = double_keys[i]

                    # Calculate position and dimensions within keys_bg_rect
                    key_x = keys_bg_rect.left + (keys_bg_rect.width / 2) * i
                    key_y = keys_bg_rect.top + (index * item_height)
                    key_rect_width = keys_bg_rect.width / 2
                    key_rect_height = item_height

                    # Check if current key is selected
                    if index == selected_vertical and selected_horizontal == i and not selected_key:
                        selected_rect = pygame.Rect(key_x, key_y, key_rect_width, key_rect_height)
                        # Draw gray rectangle covering the selected key area
                        pygame.draw.rect(self.display_surface, COLORS['dark'],
                                         selected_rect, border_radius=12)
                        pygame.draw.rect(self.display_surface, COLORS['light'],
                                         selected_rect.inflate(-6, -6), border_radius=12)
                        # Render key text in light color
                        key_text_color = COLORS['dark']
                    else:
                        # Render key text in gray color
                        key_text_color = COLORS['light']

                    # Render key text
                    if key_code:
                        key_text_surf = self.fonts['bold'].render(pygame.key.name(key_code), False, key_text_color)
                        shadow_surf = self.fonts['bold'].render(pygame.key.name(key_code), True, shadow_color)
                    else:
                        key_text_surf = self.fonts['bold'].render('Empty', False, key_text_color)
                        shadow_surf = self.fonts['bold'].render('Empty', True, shadow_color)
                    key_text_rect = key_text_surf.get_rect(
                        center=(key_x + key_rect_width / 2, key_y + key_rect_height / 2))

                    shadow_rect = key_text_rect.move(*shadow_offset)
                    self.display_surface.blit(shadow_surf, shadow_rect)

                    self.display_surface.blit(key_text_surf, key_text_rect)
                else:
                    double_keys = config_manager.settings['controls'][key_name]
                    key_code = double_keys[i]

                    # Calculate position and dimensions within keys_bg_rect
                    key_x = keys_bg_rect.left + (keys_bg_rect.width / 2) * i
                    key_y = keys_bg_rect.top + (index * item_height)
                    key_rect_width = keys_bg_rect.width / 2
                    key_rect_height = item_height

                    # Render key text
                    if key_code:
                        key_text_surf = self.fonts['bold'].render(pygame.key.name(key_code), False, COLORS['light'])
                        shadow_surf = self.fonts['bold'].render(pygame.key.name(key_code), True, shadow_color)
                    else:
                        key_text_surf = self.fonts['bold'].render('Empty', False, COLORS['light'])
                        shadow_surf = self.fonts['bold'].render('Empty', True, shadow_color)
                    key_text_rect = key_text_surf.get_rect(
                        center=(key_x + key_rect_width / 2, key_y + key_rect_height / 2))

                    shadow_rect = key_text_rect.move(*shadow_offset)
                    self.display_surface.blit(shadow_surf, shadow_rect)

                    self.display_surface.blit(key_text_surf, key_text_rect)

        if selected_key:
            # Calculate position and dimensions within keys_bg_rect
            new_key_bg_x = keys_bg_rect.left + (keys_bg_rect.width / 2) * self.ui_indexes['controls2']
            new_key_bg_y = keys_bg_rect.top + (self.ui_indexes['controls'] * item_height)
            new_key_bg_width = keys_bg_rect.width / 2
            new_key_bg_height = item_height

            # Draw keys_bg_rect with appropriate borders
            selected_rect = pygame.Rect(new_key_bg_x, new_key_bg_y, new_key_bg_width, new_key_bg_height)
            pygame.draw.rect(self.display_surface, COLORS['dark'],
                             selected_rect, border_radius=12)
            pygame.draw.rect(self.display_surface, COLORS['light'],
                             selected_rect.inflate(-6, -6), border_radius=12)

            # x for new key
            x_pos = keys_bg_rect.width / 4 + self.ui_indexes['controls2'] * keys_bg_rect.width / 2
            y_pos = self.ui_indexes['controls'] * item_height + item_height / 2
            # new key
            new_key_text = pygame.key.name(new_key) if new_key else '[enter a \n\nnew key]'
            new_key_text_surf = self.fonts['bold'].render(new_key_text, False, COLORS['dark'])
            new_key_text_rect = new_key_text_surf.get_rect(
                center=keys_bg_rect.topleft + vector(x_pos, y_pos))

            shadow_surf = self.fonts['bold'].render(pygame.key.name(new_key) if new_key else '[enter a \n\nnew key]',
                                                    True, shadow_color)
            shadow_rect = new_key_text_rect.move(*shadow_offset)
            self.display_surface.blit(shadow_surf, shadow_rect)

            self.display_surface.blit(new_key_text_surf, new_key_text_rect)

    def draw_save_menu(self):
        width, height = config_manager.settings['video']['window_width'] * 0.4, \
                        config_manager.settings['video']['window_height'] * 0.8
        bg_rect = pygame.FRect(config_manager.settings['video']['window_width'] * 0.3,
                               config_manager.settings['video']['window_height'] * 0.1, width, height)
        pygame.draw.rect(self.display_surface, COLORS['light-gray'], bg_rect, 0, 12)

        item_height = bg_rect.height / len(self.save_options)

        for index, value in enumerate(self.save_options):
            selected = index == self.ui_indexes['save']
            # text
            text_surf = self.fonts['bold'].render(value, False, COLORS['dark' if selected else 'light'])
            # rect
            text_rect = text_surf.get_frect(center=bg_rect.midtop + vector(0, item_height / 2 + index * item_height))
            text_bg_rect = pygame.FRect((0, 0), (width, item_height)).move_to(center=text_rect.center)
            # draw
            if selected:
                pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, border_radius=12)
                pygame.draw.rect(self.display_surface, COLORS['light'], text_bg_rect.inflate(-6, -6),
                                 border_radius=12)

            # Shadow effect
            shadow_offset = (2, 2)
            shadow_color = COLORS['black']
            shadow_rect = text_rect.move(*shadow_offset)
            shadow_surf = self.fonts['bold'].render(value, True, shadow_color)
            self.display_surface.blit(shadow_surf, shadow_rect)

            self.display_surface.blit(text_surf, text_rect)

    def draw_load_menu(self):
        width, height = config_manager.settings['video']['window_width'] * 0.4, \
                        config_manager.settings['video']['window_height'] * 0.8
        bg_rect = pygame.FRect(config_manager.settings['video']['window_width'] * 0.3,
                               config_manager.settings['video']['window_height'] * 0.1, width, height)
        pygame.draw.rect(self.display_surface, COLORS['light-gray'], bg_rect, 0, 12)

        item_height = bg_rect.height / len(self.load_options)

        for index, value in enumerate(self.load_options):
            selected = index == self.ui_indexes['load']
            # text
            text_surf = self.fonts['bold'].render(value, False, COLORS['dark' if selected else 'light'])
            # rect
            text_rect = text_surf.get_frect(center=bg_rect.midtop + vector(0, item_height / 2 + index * item_height))
            text_bg_rect = pygame.FRect((0, 0), (width, item_height)).move_to(center=text_rect.center)
            # draw
            if selected:
                pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, border_radius=12)
                pygame.draw.rect(self.display_surface, COLORS['light'], text_bg_rect.inflate(-6, -6),
                                 border_radius=12)

            # Shadow effect
            shadow_offset = (2, 2)
            shadow_color = COLORS['black']
            shadow_rect = text_rect.move(*shadow_offset)
            shadow_surf = self.fonts['bold'].render(value, True, shadow_color)
            self.display_surface.blit(shadow_surf, shadow_rect)

            self.display_surface.blit(text_surf, text_rect)

    # input
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
            case 'controls':
                limiter = len(self.controls_options)
            case 'save':
                limiter = len(self.save_options)
            case 'load':
                limiter = len(self.load_options)
            case _:
                limiter = 1

        # navigation
        if limiter > 0 and self.selection_mode != 'controls':
            if keys[config_manager.settings['controls']['up'][0]]\
                    or keys[config_manager.settings['controls']['up'][1]]:
                self.ui_indexes[self.selection_mode] = (self.ui_indexes[self.selection_mode] - 1) % limiter
            elif keys[config_manager.settings['controls']['down'][0]]\
                    or keys[config_manager.settings['controls']['down'][1]]:
                self.ui_indexes[self.selection_mode] = (self.ui_indexes[self.selection_mode] + 1) % limiter

        if self.selection_mode == 'audio':
            current_option = self.audio_options[self.ui_indexes[self.selection_mode]]
            if keys[config_manager.settings['controls']['left'][0]]\
                    or keys[config_manager.settings['controls']['left'][1]]:
                new_volume = max(
                    0, config_manager.settings[self.selection_mode][current_option] - 0.05
                )
                config_manager.update_setting(
                    'audio',
                    current_option,
                    new_volume
                )
                if 'adjust_audio' in self.funcs:
                    self.funcs['adjust_audio'](current_option)
            elif keys[config_manager.settings['controls']['right'][0]]\
                    or keys[config_manager.settings['controls']['right'][1]]:
                new_volume = min(
                    1, config_manager.settings[self.selection_mode][current_option] + 0.05
                )
                config_manager.update_setting(
                    'audio',
                    current_option,
                    new_volume
                )
                if 'adjust_audio' in self.funcs:
                    self.funcs['adjust_audio'](current_option)

        if self.selection_mode == 'controls':
            if keys[config_manager.settings['controls']['up'][0]]\
                    or keys[config_manager.settings['controls']['up'][1]]:
                self.ui_indexes['controls'] = (self.ui_indexes['controls'] - 1) % limiter
            elif keys[config_manager.settings['controls']['down'][0]]\
                    or keys[config_manager.settings['controls']['down'][1]]:
                self.ui_indexes['controls'] = (self.ui_indexes['controls'] + 1) % limiter
            elif keys[config_manager.settings['controls']['left'][0]]\
                    or keys[config_manager.settings['controls']['left'][1]]:
                self.ui_indexes['controls2'] = (self.ui_indexes['controls2'] - 1) % 2
            elif keys[config_manager.settings['controls']['right'][0]]\
                    or keys[config_manager.settings['controls']['right'][1]]:
                self.ui_indexes['controls2'] = (self.ui_indexes['controls2'] + 1) % 2

        if self.selection_mode == 'control_selection':
            for key_code in range(len(keys)):
                if keys[key_code] and key_code not in self.used_keys and key_code not in self.not_usable_keys:
                    self.new_key = key_code if key_code != pygame.K_BACKSPACE else 0
                    config_manager.update_setting(
                        'controls',
                        self.action_of_new_key,
                        self.new_key,
                        self.ui_indexes['controls2']
                    )
                    self.update_used_keys()
                    self.selection_mode = 'controls'
                    self.new_key = None
                    self.action_of_new_key = None
                    break  # Only handle the first pressed key

        # selection
        if keys[config_manager.settings['controls']['confirm'][0]]\
                or keys[config_manager.settings['controls']['confirm'][1]]:
            match self.selection_mode:
                case 'general':
                    match self.ui_indexes[self.selection_mode]:
                        case 0:
                            if self.main_menu:
                                self.funcs['new_game']()
                            self.reset()
                            self.running = False
                        case 1 if not self.main_menu:
                            self.selection_mode = 'save'
                        case 2:
                            self.selection_mode = 'load'
                        case 3:
                            self.selection_mode = 'settings'
                        case 4:
                            if self.main_menu:
                                pygame.quit()
                                exit()
                            else:
                                self.funcs['close_game']()
                                self.funcs['open_main_menu']()
                                self.running = False
                        case _:
                            debug("Unhandled case in 'general' selection mode")
                case 'settings':
                    match self.ui_indexes[self.selection_mode]:
                        case 0:
                            self.selection_mode = 'audio'
                        case 1:
                            self.selection_mode = 'video'
                        case 2:
                            self.selection_mode = 'controls'
                case 'video':
                    match self.ui_indexes[self.selection_mode]:
                        case 0:
                            self.selection_mode = 'resolution'
                        case 1:
                            if not pygame.display.is_fullscreen():
                                app = tk()
                                width, height = app.winfo_screenwidth(), app.winfo_screenheight()
                                set_window_size(width, height)
                                config_manager.update_setting('video', 'fullscreen', True)
                                pygame.display.toggle_fullscreen()
                                self.adjust_surface()
                                self.adjust_fonts()
                        case _:
                            debug("Unhandled case in 'video' selection mode")
                case 'resolution':
                    if int(self.display_surface.get_width()) != int(
                            self.resolution_options[self.ui_indexes[self.selection_mode]].split(' ')[0]):
                        if pygame.display.is_fullscreen():
                            pygame.display.toggle_fullscreen()
                            config_manager.update_setting('video', 'fullscreen', False)
                        set_window_size(
                            *map(int, self.resolution_options[self.ui_indexes[self.selection_mode]].split(' x ')))
                        self.adjust_surface()
                        self.adjust_fonts()
                case 'controls':
                    self.action_of_new_key = self.controls_options[self.ui_indexes[self.selection_mode]]['action']
                    self.selection_mode = 'control_selection'
                case 'save':
                    self.funcs['save'](f"sfslot{self.ui_indexes['save']}v{VERSION}.json")
                case 'load':
                    if 'load' in self.funcs:
                        if self.ui_indexes['load'] == 0:
                            filename = f"sfslotqs{VERSION}.json"
                        else:
                            filename = f"sfslot{self.ui_indexes['load'] - 1}v{VERSION}.json"
                        if filename:
                            self.funcs['load'](filename)
                        else:
                            self.funcs['load'](filename)
                        self.running = False
                        self.selection_mode = 'general'
                        self.reset()
                case _:
                    debug("Unhandled selection mode")

        # go back
        if keys[pygame.K_ESCAPE]:
            if self.selection_mode == 'general' and not self.main_menu:
                self.running = False
            elif self.selection_mode in ['settings', 'save', 'load']:
                self.selection_mode = 'general'
                self.reset()
            elif self.selection_mode in ['audio', 'video', 'controls']:
                self.selection_mode = 'settings'
                self.reset()
            elif self.selection_mode == 'resolution':
                self.selection_mode = 'video'
                self.reset()
            elif self.selection_mode == 'control_selection':
                self.selection_mode = 'controls'
                self.new_key = None
                self.action_of_new_key = None

    def reset(self):
        self.ui_indexes = {k: 0 for k in self.ui_indexes}

    # adjusting values based on option changes
    def adjust_surface(self):
        # surfaces
        self.bg_surf = pygame.transform.scale(self.bg_surf, (config_manager.settings['video']['window_width'],
                                                             config_manager.settings['video']['window_height']))
        if 'adjust_surfaces' in self.funcs:
            self.funcs['adjust_surfaces']()
        if 'adjust_fonts' in self.funcs:
            self.funcs['adjust_fonts']()

    def adjust_fonts(self):
        screen_width, _ = self.display_surface.get_size()
        font_size_ratio = 0.015
        font_size = int(screen_width * font_size_ratio)
        self.fonts = {
            'bold': pygame.font.Font(join('..', 'graphics', 'fonts', 'dogicapixelbold.otf'), font_size)
        }

    def update_used_keys(self):
        self.used_keys = list(key for key_list in config_manager.settings['controls'].values() for key in key_list)

    # run
    def run(self):
        self.running = True

        self.adjust_surface()
        self.adjust_fonts()

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
