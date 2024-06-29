import pygame

from settings import *
from config_manager import config_manager
from os.path import join
from os import walk
from pytmx.util_pygame import load_pygame


# import functions
def import_image(*path, alpha=True, file_format='png'):
    full_path = join(*path) + f'.{file_format}'
    surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()
    return surf


def import_folder(*path):
    frames = []
    for folder_path, sub_folders, image_names in walk(join(*path)):
        for image_name in sorted(image_names, key=lambda name: int(name.split('.')[0])):
            full_path = join(folder_path, image_name)
            surf = pygame.image.load(full_path).convert_alpha()
            frames.append(surf)
    return frames


def import_folder_dict(*path):
    frames = {}
    for folder_path, sub_folders, image_names in walk(join(*path)):
        for image_name in image_names:
            full_path = join(folder_path, image_name)
            surf = pygame.image.load(full_path).convert_alpha()
            frames[image_name.split('.')[0]] = surf
    return frames


def import_sub_folders(*path):
    frames = {}
    for _, sub_folders, __ in walk(join(*path)):
        if sub_folders:
            for sub_folder in sub_folders:
                frames[sub_folder] = import_folder(*path, sub_folder)
    return frames


def import_tilemap(cols, rows, *path):
    frames = {}
    surf = import_image(*path)
    cell_width, cell_height = surf.get_width() / cols, surf.get_height() / rows
    for col in range(cols):
        for row in range(rows):
            cutout_rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
            cutout_surf = pygame.Surface((cell_width, cell_height))
            cutout_surf.fill('green')
            cutout_surf.set_colorkey('green')
            cutout_surf.blit(surf, (0, 0), cutout_rect)
            frames[(col, row)] = cutout_surf
    return frames


def import_single_character(cols, rows, *path):
    frame_dict = import_tilemap(cols, rows, *path)
    new_dict = {}
    for row, direction in enumerate(('down', 'left', 'right', 'up')):
        new_dict[direction] = [frame_dict[(col, row)] for col in range(cols)]
        new_dict[f'{direction}_idle'] = [frame_dict[(0, row)]]
    return new_dict


def import_all_characters(*path):
    new_dict = {}
    for _, __, image_names in walk(join(*path)):
        for image in image_names:
            image_name = image.split('.')[0]
            new_dict[image_name] = import_single_character(4, 4, *path, image_name)
    return new_dict


def import_coastline(cols, rows, *path):
    frame_dictionary = import_tilemap(cols, rows, *path)
    new_dict = {}
    terrains = ['grass', 'grass_i', 'sand_i', 'sand', 'rock', 'rock_i', 'ice', 'ice_i']
    sides = {
        'topleft': (0, 0), 'top': (1, 0), 'topright': (2, 0),
        'bottomleft': (0, 2), 'bottom': (1, 2), 'bottomright': (2, 2),
        'left': (0, 1), 'right': (2, 1)
    }
    for index, terrain in enumerate(terrains):
        new_dict[terrain] = {}
        for key, pos in sides.items():
            new_dict[terrain][key] = [frame_dictionary[pos[0] + index * 3, pos[1] + row] for row in range(0, rows, 3)]
    return new_dict


def import_tmx_maps(*path):
    tmx_dict = {}
    for folder_path, sub_folder, file_names in walk(join(*path)):
        for file in file_names:
            tmx_dict[file.split('.')[0]] = load_pygame(join(folder_path, file))
    return tmx_dict


def import_monster(cols, rows, *path):
    monster_dict = {}
    for folder_path, sub_folders, image_names in walk(join(*path)):
        for image in image_names:
            image_name = image.split('.')[0]
            monster_dict[image_name] = {}
            frame_dict = import_tilemap(cols, rows, *path, image_name)
            for row, key in enumerate(('idle', 'attack')):
                monster_dict[image_name][key] = [frame_dict[(col, row)] for col in range(cols)]
    return monster_dict


def import_attacks(*path):
    attack_dict = {}
    for folder_path, _, image_names in walk(join(*path)):
        for image in image_names:
            image_name = image.split('.')[0]
            attack_dict[image_name] = list(import_tilemap(4, 1, folder_path, image_name).values())
    return attack_dict


def audio_importer(*path):
    files = {}
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            files[file_name.split('.')[0]] = pygame.mixer.Sound(full_path)
    return files


# game functions
def check_connection(radius, entity, target, tolerance=5):
    relation = vector(target.rect.center) - vector(entity.rect.center)
    if relation.length() < radius:
        if entity.facing_direction == 'left' and relation.x < 0 and abs(relation.y) < tolerance or\
                entity.facing_direction == 'right' and relation.x > 0 and abs(relation.y) < tolerance or\
                entity.facing_direction == 'up' and relation.y < 0 and abs(relation.x) < tolerance or\
                entity.facing_direction == 'down' and relation.y > 0 and abs(relation.x) < tolerance:
            return True


def draw_bar(surf, rect, value, max_value, color, bg_color, radius=1):
    ratio = rect.width / max_value
    bg_rect = rect.copy()
    progress = max(0, min(rect.width, value * ratio))
    progress_rect = pygame.FRect(rect.topleft, (progress, rect.height))
    pygame.draw.rect(surf, bg_color, bg_rect, 0, radius)
    pygame.draw.rect(surf, color, progress_rect, 0, radius)


def outline_creator(frame_dict, width):
    outline_frame_dict = {}
    for monster, monster_frames in frame_dict.items():
        outline_frame_dict[monster] = {}
        for state, frames in monster_frames.items():
            outline_frame_dict[monster][state] = []
            for frame in frames:
                new_surf = pygame.Surface(vector(frame.get_size()) + vector(width * 2), pygame.SRCALPHA)
                new_surf.fill((0, 0, 0, 0))
                white_frame = pygame.mask.from_surface(frame).to_surface()
                white_frame.set_colorkey('black')

                new_surf.blit(white_frame, (0, 0))  # topleft
                new_surf.blit(white_frame, (width, 0))  # top
                new_surf.blit(white_frame, (width*2, 0))  # topright
                new_surf.blit(white_frame, (width*2, width))  # right
                new_surf.blit(white_frame, (width*2, width*2))  # bottomright
                new_surf.blit(white_frame, (width, width*2))  # bottom
                new_surf.blit(white_frame, (0, width*2))  # bottomleft
                new_surf.blit(white_frame, (0, width))  # left
                outline_frame_dict[monster][state].append(new_surf)
    return outline_frame_dict


# settings functions
def set_window_size(width, height):
    x = (1920-width)//2
    y = (1000-height)//2 + 30
    config_manager.update_setting('video', 'window_width', width)
    config_manager.update_setting('video', 'window_height', height)
    pygame.display.set_window_position((x, y))
    pygame.display.set_mode((width, height), pygame.RESIZABLE)
