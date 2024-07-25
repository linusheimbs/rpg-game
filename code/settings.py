import pygame
from pygame.math import Vector2 as vector
from sys import exit

VERSION = '0.6'
TILE_SIZE = 64
ANIMATION_SPEED = 6
BATTLE_OUTLINE_WIDTH = 4

COLORS = {
    'white': '#f4fefa',
    'pure white': '#ffffff',
    'dark white': '#f0f0f0',
    'dark': '#2b292c',
    'light': '#c8c8c8',
    'gray': '#3a373b',
    'gold': '#ffd700',
    'light-gray': '#4b484d',
    'black': '#000000',
    'red': '#f03131',
    'blue': '#66d7ee',
    'normal': '#ffffff',
    'fire': '#c3362b',
    'water': '#50b0d8',
    'plant': '#4caf50',
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
    'monster': 1,
    'name': 2,
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
