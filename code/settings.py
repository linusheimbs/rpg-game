import pygame
from pygame.math import Vector2 as vector
from sys import exit

WINDOW_WIDTH, WINDOW_HEIGHT = 1600, 900
TILE_SIZE = 64

START_POS = 'world'

ANIMATION_SPEED = 6
BATTLE_OUTLINE_WIDTH = 4

AUDIO = {
    'all': 0.1
}

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

BATTLE_POSITIONS = {
    'left': {
        'top': (0.25 * WINDOW_WIDTH, 0.27 * WINDOW_HEIGHT),
        'center': (0.17 * WINDOW_WIDTH, 0.54 * WINDOW_HEIGHT),
        'bottom': (0.30 * WINDOW_WIDTH, 0.80 * WINDOW_HEIGHT)
    },
    'right': {
        'top': (0.75 * WINDOW_WIDTH, 0.27 * WINDOW_HEIGHT),
        'center': (0.85 * WINDOW_WIDTH, 0.55 * WINDOW_HEIGHT),
        'bottom': (0.78 * WINDOW_WIDTH, 0.82 * WINDOW_HEIGHT)
    }
}

BATTLE_LAYERS = {
    'outline': 0,
    'name': 1,
    'monster': 2,
    'effects': 3,
    'overlay': 4
}

BATTLE_CHOICES = {
    'full': {
        'fight': {'pos': vector(WINDOW_WIDTH * 0.023, WINDOW_HEIGHT * -0.083), 'icon': 'sword'},
        'defend': {'pos': vector(WINDOW_WIDTH * 0.031, WINDOW_HEIGHT * -0.027), 'icon': 'shield'},
        'switch': {'pos': vector(WINDOW_WIDTH * 0.031, WINDOW_HEIGHT * 0.027), 'icon': 'arrows'},
        'catch': {'pos': vector(WINDOW_WIDTH * 0.023, WINDOW_HEIGHT * 0.083), 'icon': 'hand'}
    },

    'limited': {
        'fight': {'pos': vector(WINDOW_WIDTH * 0.023, WINDOW_HEIGHT * -0.055), 'icon': 'sword'},
        'defend': {'pos': vector(WINDOW_WIDTH * 0.031, WINDOW_HEIGHT * 0.0), 'icon': 'shield'},
        'switch': {'pos': vector(WINDOW_WIDTH * 0.023, WINDOW_HEIGHT * 0.055), 'icon': 'arrows'}
    }
}

ELEMENT_RELATIONSHIPS = {
    'fire': {
        'vulnerable_to': ['water'],
        'resistant_to': ['plant']
    },
    'water': {
        'vulnerable_to': ['plant'],
        'resistant_to': ['fire']
    },
    'plant': {
        'vulnerable_to': ['fire'],
        'resistant_to': ['water']
    }
}

SHOW_HITBOX = False
