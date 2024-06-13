import pygame
from settings import *
from support import draw_bar
from game_data import MONSTER_DATA, ATTACK_DATA


class MonsterInventory:
    def __init__(self, monsters, fonts, monster_frames):
        self.display_surface = pygame.display.get_surface()
        self.fonts = fonts
        self.monsters = monsters

        # frames
        self.icon_frames = monster_frames['icons']
        self.monster_frames = monster_frames['monsters']
        self.monster_frame_index = 0
        self.ui_frames = monster_frames['ui']

        # tint surf
        self.tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.tint_surf.set_alpha(200)

        # dimensions
        self.main_rect = pygame.FRect(0, 0, WINDOW_WIDTH * 0.7, WINDOW_HEIGHT * 0.85)\
            .move_to(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))

        # list
        self.visible_items = 6
        self.list_width = self.main_rect.width * 0.33
        self.item_height = self.main_rect.height / self.visible_items
        self.index = 0
        self.selected_index = None

        # max values
        self.max_stats = {}
        for data in MONSTER_DATA.values():
            for stat, value in data['stats'].items():
                if stat != 'element':
                    if stat not in self.max_stats:
                        self.max_stats[stat] = value
                    else:
                        self.max_stats[stat] = value if value > self.max_stats[stat] else self.max_stats[stat]
        self.max_stats['health'] = self.max_stats.pop('max_health')
        self.max_stats['energy'] = self.max_stats.pop('max_energy')

    def input(self):
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_w]:
            self.index -= 1
        if keys[pygame.K_s]:
            self.index += 1
        if keys[pygame.K_f] or keys[pygame.K_SPACE]:
            if self.selected_index is not None:
                selected_monster = self.monsters[self.selected_index]
                current_monster = self.monsters[self.index]
                self.monsters[self.index] = selected_monster
                self.monsters[self.selected_index] = current_monster
                self.selected_index = None
            else:
                self.selected_index = self.index

        self.index = self.index % len(self.monsters)

    def display_list(self):
        # background
        bg_rect = pygame.FRect(self.main_rect.topleft, (self.list_width, self.main_rect.height))
        pygame.draw.rect(self.display_surface, COLORS['gray'], bg_rect, 0, 0, 12, 0, 12, 0)

        v_offset = 0 if self.index < self.visible_items else -(self.index - self.visible_items + 1) * self.item_height
        for index, monster in self.monsters.items():
            # colors
            bg_color = COLORS['gray'] if self.index != index else COLORS['light']
            text_color = COLORS['white'] if self.selected_index != index else COLORS['gold']

            top = self.main_rect.top + index * self.item_height + v_offset
            item_rect = pygame.FRect(self.main_rect.left, top, self.list_width, self.item_height)

            text_surf = self.fonts['regular'].render(monster.name, False, text_color)
            text_rect = text_surf.get_frect(midleft=item_rect.midleft + vector(100, 0))

            icon_surf = self.icon_frames[monster.name]
            icon_rect = icon_surf.get_frect(center=item_rect.midleft + vector(50, 0))

            if item_rect.colliderect(self.main_rect):
                # check corners
                if item_rect.collidepoint(self.main_rect.topleft):
                    pygame.draw.rect(self.display_surface, bg_color, item_rect, 0, 0, 12)
                elif item_rect.collidepoint(self.main_rect.bottomleft + vector(1, -1)):
                    pygame.draw.rect(self.display_surface, bg_color, item_rect, 0, 0, 0, 0, 12, 0)
                else:
                    pygame.draw.rect(self.display_surface, bg_color, item_rect)

                self.display_surface.blit(text_surf, text_rect)
                self.display_surface.blit(icon_surf, icon_rect)

        # lines between monsters
        for i in range(1, min(self.visible_items, len(self.monsters))):
            y = self.main_rect.top + self.item_height * i
            left = self.main_rect.left
            right = self.main_rect.left + self.list_width
            pygame.draw.line(self.display_surface, COLORS['light-gray'], (left, y), (right, y))

        # Display slider if necessary
        total_items = len(self.monsters)
        if total_items > self.visible_items:
            # color
            slider_color = COLORS['light-gray']

            slider_width = 10
            slider_height = self.main_rect.height * (self.visible_items / total_items)
            slider_pos_y = self.main_rect.top + (self.index / max(1, total_items - 1)) * (
                        self.main_rect.height - slider_height + 1)

            slider_rect = pygame.FRect(self.main_rect.left, slider_pos_y, slider_width, slider_height)
            if slider_rect.collidepoint(self.main_rect.topleft):
                pygame.draw.rect(self.display_surface, slider_color, slider_rect, 0, 0, 12)
            elif slider_rect.collidepoint(self.main_rect.bottomleft + vector(1, -1)):
                pygame.draw.rect(self.display_surface, slider_color, slider_rect, 0, 0, 0, 0, 12, 0)
            else:
                pygame.draw.rect(self.display_surface, slider_color, slider_rect)

        # shadow
        shadow_surf_width = 4
        shadow_surf = pygame.Surface((shadow_surf_width, self.main_rect.height))
        shadow_surf.set_alpha(50)
        self.display_surface.blit(shadow_surf, (self.main_rect.left + self.list_width - shadow_surf_width,
                                                self.main_rect.top))

    def display_main(self, dt):
        # data
        monster = self.monsters[self.index]

        # main bg
        main_rect = pygame.FRect(self.main_rect.left + self.list_width, self.main_rect.top,
                                 self.main_rect.width - self.list_width, self.main_rect.height)
        pygame.draw.rect(self.display_surface, COLORS['dark'], main_rect, 0, 12, 0, 12, 0)

        # monster display
        top_rect = pygame.FRect(main_rect.topleft, (main_rect.width, main_rect.height * 0.4))
        self.display_monster(monster, top_rect, dt)

        # health and energy
        bar_data = {
            'width': main_rect.width * 0.45,
            'height': 30,
            'top': top_rect.bottom + main_rect.width * 0.03,
            'left_side': main_rect.left + main_rect.width / 4,
            'right_side': main_rect.left + main_rect.width * 3 / 4
        }
        # health
        self.display_health_bar(monster, bar_data)
        # energy
        self.display_energy_bar(monster, bar_data)

        # info
        info_top = top_rect.bottom + main_rect.height * 0.08

        # stats
        self.display_stats(monster, main_rect, info_top)

        # abilities
        self.display_abilities(monster, main_rect, info_top)

    def display_monster(self, monster, top_rect, dt):
        # color themed bg
        pygame.draw.rect(self.display_surface, COLORS[monster.element], top_rect, 0, 0, 0, 12)

        # monster animation
        self.monster_frame_index += ANIMATION_SPEED * dt
        self.monster_frame_index %= len(self.monster_frames[monster.name]['idle'])
        monster_surf = self.monster_frames[monster.name]['idle'][int(self.monster_frame_index)]
        monster_rect = monster_surf.get_frect(center=top_rect.center)
        self.display_surface.blit(monster_surf, monster_rect)

        # name
        name_surf = self.fonts['bold'].render(monster.name, False,
                                              COLORS['white' if monster.element != 'normal' else 'black'])
        name_rect = name_surf.get_frect(topleft=top_rect.topleft + vector(10, 10))
        self.display_surface.blit(name_surf, name_rect)

        # level
        level_surf = self.fonts['regular'].render(f'Level: {monster.level}', False,
                                                  COLORS['white' if monster.element != 'normal' else 'black'])
        level_rect = level_surf.get_frect(bottomleft=top_rect.bottomleft + vector(10, -14))
        self.display_surface.blit(level_surf, level_rect)
        # exp
        draw_bar(
            surf=self.display_surface,
            rect=pygame.FRect(level_rect.bottomleft, (100, 4)),
            value=monster.exp,
            max_value=monster.level_up,
            color=COLORS['white' if monster.element != 'normal' else 'light-gray'],
            bg_color=COLORS['dark']
        )

        # element
        element_surf = self.fonts['regular'].render(f'{monster.element}', False,
                                                    COLORS['white'] if monster.element != 'normal' else 'black')
        element_rect = element_surf.get_frect(bottomright=top_rect.bottomright + vector(-10, -10))
        self.display_surface.blit(element_surf, element_rect)

    def display_health_bar(self, monster, bar_data):
        hp_bar_rect = pygame.FRect((0, 0), (bar_data['width'], bar_data['height'])).move_to(
            midtop=(bar_data['left_side'], bar_data['top']))
        draw_bar(
            surf=self.display_surface,
            rect=hp_bar_rect,
            value=monster.health,
            max_value=monster.get_stat('max_health'),
            color=COLORS['red'],
            bg_color=COLORS['black'],
            radius=2
        )
        hp_text = self.fonts['regular'].render(f'HP: {int(monster.health)}/{monster.get_stat("max_health")}',
                                               False, COLORS['white'])
        hp_rect = hp_text.get_frect(midleft=hp_bar_rect.midleft + vector(10, 0))
        self.display_surface.blit(hp_text, hp_rect)

    def display_energy_bar(self, monster, bar_data):
        ep_bar_rect = pygame.FRect((0, 0), (bar_data['width'], bar_data['height'])).move_to(
            midtop=(bar_data['right_side'], bar_data['top']))
        draw_bar(
            surf=self.display_surface,
            rect=ep_bar_rect,
            value=monster.energy,
            max_value=monster.get_stat('max_energy'),
            color=COLORS['blue'],
            bg_color=COLORS['black'],
            radius=2
        )
        ep_text = self.fonts['regular'].render(f'EP: {int(monster.energy)}/{monster.get_stat("max_energy")}',
                                               False, COLORS['white'])
        ep_rect = ep_text.get_frect(midleft=ep_bar_rect.midleft + vector(10, 0))
        self.display_surface.blit(ep_text, ep_rect)

    def display_stats(self, monster, main_rect, info_top):
        stats_rect = pygame.FRect(main_rect.left + main_rect.width * 0.05, info_top, main_rect.width * 0.42,
                                  main_rect.height * 0.5)
        stats_text_surf = self.fonts['regular'].render('Stats', False, COLORS['white'])
        stats_text_rect = stats_text_surf.get_frect(topleft=stats_rect.topleft)
        self.display_surface.blit(stats_text_surf, stats_text_rect)

        monster_stats = monster.get_stats()
        stat_height = stats_rect.height / len(monster_stats)
        for index, (stat, value) in enumerate(monster_stats.items()):
            single_stat_rect = pygame.FRect(stats_rect.left, stats_rect.top + index * stat_height, stats_rect.width,
                                            stat_height)

            # icon
            icon_surf = self.ui_frames[stat]
            icon_rect = icon_surf.get_frect(midleft=single_stat_rect.midleft)
            self.display_surface.blit(icon_surf, icon_rect)

            # text
            stat_text_surf = self.fonts['regular'].render(stat, False, COLORS['white'])
            text_rect = stat_text_surf.get_frect(topleft=icon_rect.topleft + vector(20, -7))
            self.display_surface.blit(stat_text_surf, text_rect)

            # bar
            bar_rect = pygame.FRect((text_rect.left, text_rect.bottom + 2),
                                    (single_stat_rect.width - (text_rect.left - single_stat_rect.left), 4))
            draw_bar(
                surf=self.display_surface,
                rect=bar_rect, value=value,
                max_value=self.max_stats[stat] * monster.level,
                color=COLORS['white'],
                bg_color=COLORS['black'],
                radius=2
            )

    def display_abilities(self, monster, main_rect, info_top):
        abilities_rect = pygame.FRect(main_rect.left + main_rect.width * 0.55, info_top, main_rect.width * 0.4,
                                      main_rect.height * 0.5)
        abilities_text_surf = self.fonts['regular'].render('Ability', False, COLORS['white'])
        ability_text_rect = abilities_text_surf.get_frect(topleft=abilities_rect.topleft)
        self.display_surface.blit(abilities_text_surf, ability_text_rect)

        for index, ability in enumerate(monster.get_abilities()):
            element = ATTACK_DATA[ability]['element']
            ability_text_surf = self.fonts['regular'].render(ability, False, COLORS['black'])
            x = abilities_rect.left + index % 2 * abilities_rect.width / 2
            y = (abilities_rect.top + ability_text_rect.height * 2) + (index//2 * (ability_text_surf.get_height() * 6))
            ability_rect = ability_text_surf.get_frect(topleft=(x, y))
            pygame.draw.rect(self.display_surface, COLORS[element], ability_rect.inflate(10, 10), 0, 4)
            self.display_surface.blit(ability_text_surf, ability_rect)

    def update(self, dt):
        self.input()
        self.display_surface.blit(self.tint_surf, (0, 0))
        self.display_list()
        self.display_main(dt)
