import pygame
from pygame.math import Vector2 as vector
from sys import exit

settings = {
    'window': {
        'window_width': 1600, 'window_height': 900
    },
    'audio': {
        'all': 0.0
    },
    'show_hitbox': False
}


def set_window_size(width, height):
    settings['window']['window_width'] = width
    settings['window']['window_height'] = height
    pygame.display.set_mode((width, height), pygame.RESIZABLE)
    if width == 1920:
        pygame.display.toggle_fullscreen()


TILE_SIZE = 64

START_POS = 'world'
ANIMATION_SPEED = 6
BATTLE_OUTLINE_WIDTH = 4

COLORS = {
    'white': '#f4fefa',
    'pure white': '#ffffff',
    'dark': '#2b292c',
    'light': '#c8c8c8',
    'gray': '#3a373b',
    'gold': '#ffd700',
    'light-gray': '#4b484d',
    'black': '#000000',
    'red': '#f03131',
    'blue': '#66d7ee',
    'fire': '#c3362b',
    'water': '#50b0d8',
    'plant': '#4caf50',
    'normal': '#ffffff',
    'dark white': '#f0f0f0'
}

WORLD_LAYERS = {
    'water': 0,
    'bg': 1,
    'shadow': 2,
    'main': 3,
    'top': 4
}

BATTLE_LAYERS = {
    'outline': 0,
    'name': 1,
    'monster': 2,
    'effects': 3,
    'overlay': 4
}

ELEMENT_RELATIONSHIPS = {
    'normal': {
        'vulnerable_to': [],
        'resistant_to': []
    },
    'fire': {
        'vulnerable_to': ['water'],
        'resistant_to': ['fire', 'plant']
    },
    'water': {
        'vulnerable_to': ['plant'],
        'resistant_to': ['water', 'fire']
    },
    'plant': {
        'vulnerable_to': ['fire'],
        'resistant_to': ['plant', 'water']
    }
}
