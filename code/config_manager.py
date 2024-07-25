import pygame

from tkinter import Tk as tk
from settings import *
import json
import os
from debug import debug


class ConfigManager:
    def __init__(self, filepath='../save_data/settings.json'):
        self.filepath = filepath
        app = tk()
        width, height = app.winfo_screenwidth(), app.winfo_screenheight()
        self.settings = {
            'video': {
                'window_width': width, 'window_height': height,
                'fullscreen': True
            },
            'audio': {
                'music': 0.,
                'sfx': 0.
            },
            'controls': {
                'up': [pygame.K_w, 0],
                'down': [pygame.K_s, 0],
                'left': [pygame.K_a, 0],
                'right': [pygame.K_d, 0],
                'confirm': [pygame.K_f, pygame.K_SPACE],
                'inventory': [pygame.K_i, pygame.K_TAB],
            },
            'show_hitbox': False
        }
        # self.load_settings()
        self.ensure_directory_exists()

    def ensure_directory_exists(self):
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

    def load_settings(self):
        try:
            with open(self.filepath, 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            self.save_settings()

    def save_settings(self):
        with open(self.filepath, 'w') as file:
            json.dump(self.settings, file, indent=4)

    def update_setting(self, category, key, value, control=None):
        if category in self.settings and key in self.settings[category]:
            if control:
                self.settings[category][key][control] = value
            else:
                self.settings[category][key] = value
            self.save_settings()
        else:
            debug("Invalid setting key or category")


config_manager = ConfigManager()
