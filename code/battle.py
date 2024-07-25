import pygame.sprite

from settings import *
from config_manager import config_manager
from sprites import MonsterSprite, MonsterNameSprite, MonsterLevelSprite, MonsterStatsSprite, MonsterOutlineSprite, \
    AttackSprite, TimedSprite
from groups import BattleSprites
from game_data import game_data
from support import draw_bar
from timer import Timer
from random import choice
from debug import debug


class Battle:
    # main
    def __init__(self, player_monsters, opponent_monsters, monster_frames, bg_surf, fonts, end_battle, character,
                 check_evolution, sounds):
        self.draw_actions = False
        # general
        self.display_surface = pygame.display.get_surface()
        self.monster_data = {
            'player': [monster for monster in player_monsters.values()],
            'opponent': [monster for monster in opponent_monsters.values()]
        }
        self.player_monsters_ref = player_monsters
        self.monster_frames = monster_frames
        self.window_width = config_manager.settings['video']['window_width']
        self.window_height = config_manager.settings['video']['window_height']
        self.bg_surf = pygame.transform.scale(bg_surf, (self.window_width, self.window_height))
        self.fonts = fonts
        self.battle_over = False
        self.end_battle = end_battle
        self.character = character
        self.check_evolution = check_evolution

        self.battle_positions = {
            'left': {
                'top': (0.25 * self.window_width, 0.30 * self.window_height),
                'center': (0.15 * self.window_width, 0.57 * self.window_height),
                'bottom': (0.22 * self.window_width, 0.84 * self.window_height)
            },
            'right': {
                'top': (0.75 * self.window_width, 0.31 * self.window_height),
                'center': (0.85 * self.window_width, 0.58 * self.window_height),
                'bottom': (0.78 * self.window_width, 0.85 * self.window_height)
            }
        }

        self.battle_choices = {
            'full': {
                'fight': {'pos': vector(self.window_width * 0.023, self.window_height * -0.088), 'icon': 'sword'},
                'defend': {'pos': vector(self.window_width * 0.031, self.window_height * -0.044),
                           'icon': 'shield'},
                'switch': {'pos': vector(self.window_width * 0.032, self.window_height * 0), 'icon': 'arrows'},
                'catch': {'pos': vector(self.window_width * 0.031, self.window_height * 0.044), 'icon': 'hand'},
                'exit': {'pos': vector(self.window_width * 0.023, self.window_height * 0.088),
                         'icon': 'cross_small'}
            },

            'limited': {
                'fight': {'pos': vector(self.window_width * 0.023, self.window_height * -0.066), 'icon': 'sword'},
                'defend': {'pos': vector(self.window_width * 0.031, self.window_height * -0.022), 'icon': 'shield'},
                'switch': {'pos': vector(self.window_width * 0.031, self.window_height * 0.022), 'icon': 'arrows'},
                'exit': {'pos': vector(self.window_width * 0.023, self.window_height * 0.066),
                         'icon': 'cross_small'}
            }
        }

        # groups
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()

        self.all_monsters = self.player_sprites.sprites() + self.opponent_sprites.sprites()
        self.all_monsters.sort(key=lambda monster_sprite: monster_sprite.monster.get_stat('speed'), reverse=True)
        self.available_monsters = None

        # control
        self.current_monster = None
        self.selected_attack = None
        self.selected = False
        self.selection_mode = None
        self.selection_side = 'player'
        self.ui_indexes = {
            'general': 0,
            'monster': 0,
            'attacks': 0,
            'defend': 0,
            'switch': 0,
            'target': 0
        }

        # turn
        self.turn = False
        self.turn_index = 0
        self.actions_list = []
        self.action_index = 0
        self.executing_actions = False

        # timer
        self.timers = {
            'action': Timer(1000, func=self.execute_actions)
        }

        self.setup()

        # sounds
        self.sounds = sounds

        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            monster_sprite.monster.paused = False

    # setup
    def setup(self):
        for entity, monsters in self.monster_data.items():
            alive_monsters = [monster for monster in monsters if monster.health > 0]

            for index, monster in enumerate(alive_monsters[:3]):
                self.create_monster(monster, index, index, entity)

        monster_to_remove = min(len(self.monster_data['opponent']), 3)
        for _ in range(monster_to_remove):
            self.monster_data['opponent'].pop(0)

    def create_monster(self, monster, index, pos_index, entity):
        frames = self.monster_frames['monsters'][monster.name]
        outline_frames = self.monster_frames['outlines'][monster.name]
        if entity == 'player':
            pos = list(self.battle_positions['left'].values())[pos_index]
            groups = (self.battle_sprites, self.player_sprites)
            frames = {state: [pygame.transform.flip(frame, True, False)
                              for frame in frames] for state, frames in frames.items()}
            outline_frames = {state: [pygame.transform.flip(frame, True, False)
                                      for frame in frames] for state, frames in outline_frames.items()}
        else:
            pos = list(self.battle_positions['right'].values())[pos_index]
            groups = (self.battle_sprites, self.opponent_sprites)

        monster_sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity, self.apply_attack,
                                       self.create_monster)
        MonsterOutlineSprite(monster_sprite, self.battle_sprites, outline_frames)

        # ui
        name_pos = monster_sprite.rect.topleft if entity == 'player' else monster_sprite.rect.topright
        name_sprite = MonsterNameSprite(name_pos, monster_sprite, self.battle_sprites, self.fonts['regular'])
        anchor = name_sprite.rect.bottomleft if entity == 'player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity, anchor, monster_sprite, self.battle_sprites, self.fonts['small'])
        MonsterStatsSprite(monster_sprite.rect.midbottom + vector(0, 30), monster_sprite, (150, 48),
                           self.battle_sprites, self.fonts['small'])

    # input
    def input(self):
        if self.selection_mode and self.current_monster and not self.selected:
            keys = pygame.key.get_just_pressed()

            match self.selection_mode:
                case 'general':
                    limiter = len(self.battle_choices['limited' if self.character else 'full'])
                case 'attacks':
                    limiter = len(self.current_monster.monster.get_abilities())
                case 'target':
                    limiter = len(self.opponent_sprites) if self.selection_side == 'opponent'\
                        else len(self.player_sprites)
                case 'defend':
                    limiter = 2
                case 'switch':
                    limiter = len(self.available_monsters)
                case _:
                    limiter = 1

            if limiter > 0:
                # up
                if keys[config_manager.settings['controls']['up'][0]]\
                        or keys[config_manager.settings['controls']['up'][1]]:
                    self.ui_indexes[self.selection_mode] = (self.ui_indexes[self.selection_mode] - 1) % limiter
                # down
                if keys[config_manager.settings['controls']['down'][0]]\
                        or keys[config_manager.settings['controls']['down'][1]]:
                    self.ui_indexes[self.selection_mode] = (self.ui_indexes[self.selection_mode] + 1) % limiter

            # confirm
            if keys[config_manager.settings['controls']['confirm'][0]]\
                    or keys[config_manager.settings['controls']['confirm'][1]]:
                # target
                match self.selection_mode:
                    case 'target':
                        sprite_group = self.opponent_sprites if self.selection_side == 'opponent'\
                            else self.player_sprites
                        sprites = {sprite.pos_index: sprite for sprite in sprite_group}
                        monster_sprite = sprites[list(sprites.keys())[self.ui_indexes['target']]]

                        if self.selected_attack:
                            if (self.current_monster.monster.energy >=
                                    game_data.attack_data[self.selected_attack]['cost']):
                                self.selected = True
                                self.actions_list.append(
                                    {
                                        'index': self.turn_index,
                                        'action': 'activate_attack',
                                        'selected_attack': self.selected_attack,
                                        'target': monster_sprite
                                    }
                                )
                                self.next_turn()
                            else:
                                TimedSprite(self.current_monster.rect.center, self.monster_frames['ui']['cross'],
                                            self.battle_sprites, 1000)
                        else:
                            if monster_sprite.monster.health < monster_sprite.monster.get_stat('max_health') * 0.9:
                                self.selected = True
                                self.actions_list.append(
                                    {
                                        'index': self.turn_index,
                                        'action': 'catch',
                                        'target': monster_sprite
                                    }
                                )
                                self.next_turn()
                            else:
                                TimedSprite(monster_sprite.rect.center, self.monster_frames['ui']['cross'],
                                            self.battle_sprites, 1000)
                    case 'attacks':
                        self.selection_mode = 'target'
                        self.selected_attack = self.current_monster.monster.get_abilities(
                            all_abilities=False)[self.ui_indexes['attacks']]
                        self.selection_side = game_data.attack_data[self.selected_attack]['side']
                        self.ui_indexes = {k: 0 for k in self.ui_indexes}
                    case 'defend':
                        if self.ui_indexes['defend'] == 0:
                            if self.current_monster.monster.energy > 0 and not self.current_monster.monster.defending:
                                self.current_monster.monster.defending = True
                                self.current_monster.monster.energy -= 1
                                if self.current_monster.monster.energy <= 0:
                                    self.selected = True
                                    self.next_turn()
                                else:
                                    self.selection_mode = 'general'
                            else:
                                TimedSprite(self.current_monster.rect.center, self.monster_frames['ui']['cross'],
                                            self.battle_sprites, 1000)
                        elif self.ui_indexes['defend'] == 1:
                            self.selection_mode = 'general'
                    case 'switch':
                        if self.available_monsters.items():
                            self.selected = True
                            new_monster = list(self.available_monsters.items())[self.ui_indexes['switch']]
                            new_monster_index = self.turn_index
                            self.current_monster.kill()
                            self.create_monster(new_monster[1], new_monster[0],
                                                self.all_monsters[new_monster_index].pos_index, 'player')
                            self.player_sprites = pygame.sprite.Group(
                                sorted(self.player_sprites.sprites(), key=lambda sprite: sprite.pos_index))
                            self.next_turn()
                        else:
                            self.selection_mode = 'general'
                    case 'general':
                        if self.ui_indexes['general'] == 0:
                            self.selection_mode = 'attacks'
                        if self.ui_indexes['general'] == 1:
                            self.selection_mode = 'defend'
                        if self.ui_indexes['general'] == 2:
                            self.selection_mode = 'switch'
                        if self.ui_indexes['general'] == 3 and not self.character:
                            # catch
                            self.selection_mode = 'target'
                            self.selection_side = 'opponent'
                        if self.ui_indexes['general'] == 4 or (self.ui_indexes['general'] == 3 and self.character):
                            self.selected = True
                            self.next_turn()
                    case _:
                        debug(f"Unknown mode: {self.selection_mode}")

            # going back
            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ('attacks', 'switch', 'defend'):
                    self.selection_mode = 'general'
                    for item in self.ui_indexes:
                        if item != 'general':
                            self.ui_indexes[item] = 0
                elif self.selection_mode == 'target':
                    self.selection_mode = 'general'
                    self.selection_side = 'player'
                    self.selected_attack = None
                    for item in self.ui_indexes:
                        if item != 'general':
                            self.ui_indexes[item] = 0

    # drawing ui
    def draw_ui(self):
        if self.current_monster:
            match self.selection_mode:
                case 'general':
                    self.draw_general()
                case 'attacks':
                    self.draw_attacks()
                case 'defend':
                    self.draw_defend()
                case 'switch':
                    self.draw_switch()
                case _:
                    pass

    def draw_general(self):
        for index, (option, data_dict) in enumerate(
                self.battle_choices['limited' if self.character else 'full'].items()):
            if index == self.ui_indexes['general']:
                surf = self.monster_frames['ui'][data_dict['icon']]
            else:
                surf = pygame.transform.grayscale(self.monster_frames['ui'][data_dict['icon']])
            rect = surf.get_frect(center=self.current_monster.rect.midright + data_dict['pos'])
            self.display_surface.blit(surf, rect)

    def draw_attacks(self):
        # data
        abilities = self.current_monster.monster.get_abilities(all_abilities=False)
        width, height = self.window_width * 0.1, self.window_height * 0.2
        visible_attacks = 6
        item_height = height / visible_attacks

        # bg
        bg_rect = pygame.FRect((0, 0), (width, height)).move_to(
            midleft=self.current_monster.rect.midright + vector(self.window_width * 0.023, 0))
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        # fg
        for index, ability in enumerate(abilities):
            selected = index == self.ui_indexes['attacks']
            # text
            if selected:
                element = game_data.attack_data[ability]['element']
                text_color = COLORS[element]
            else:
                text_color = COLORS['black']
            text_surf = self.fonts['regular'].render(ability, False, text_color)
            # rect
            text_rect = text_surf.get_frect(
                center=bg_rect.midtop + vector(0, item_height / 2 + index * item_height))
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

    def draw_defend(self):
        # data
        width, height = self.window_width * 0.1, self.window_height * 0.1
        item_height = height / 2

        # bg
        bg_rect = pygame.FRect((0, 0), (width, height)).move_to(midleft=self.current_monster.rect.midright + vector(
            self.window_width * 0.023, 0))
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        # fg
        for index, text in enumerate(['Confirm', 'Back']):
            selected = index == self.ui_indexes['defend']
            # text
            if selected:
                text_color = COLORS['white']
            else:
                text_color = COLORS['black']
            text_surf = self.fonts['regular'].render(text, False, text_color)
            # rect
            text_rect = text_surf.get_frect(
                center=bg_rect.midtop + vector(0, item_height / 2 + index * item_height))
            text_bg_rect = pygame.FRect((0, 0), (width, item_height)).move_to(center=text_rect.center)
            # draw
            if bg_rect.collidepoint(text_rect.center):
                if selected:
                    if text_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, 0, 0, 5, 5)
                    else:
                        pygame.draw.rect(self.display_surface, COLORS['dark'], text_bg_rect, 0, 0, 0, 0, 5, 5)
                self.display_surface.blit(text_surf, text_rect)

    def draw_switch(self):
        # data
        width, height = self.window_width * 0.25, self.window_height * 0.35
        visible_monsters = 4
        item_height = height / visible_monsters
        v_offset = 0 if self.ui_indexes['switch'] < visible_monsters else \
            -(self.ui_indexes['switch'] - visible_monsters + 1) * item_height

        # bg
        bg_rect = pygame.FRect((0, 0), (width, height)).move_to(
            midleft=self.current_monster.rect.midright + vector(self.window_width * 0.023, 0))
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        # monsters
        active_monsters = [monster_sprite.monster for monster_sprite in self.player_sprites]
        self.available_monsters = {index: monster for index, monster in enumerate(self.monster_data['player'])
                                   if monster.health > 0 and monster not in active_monsters}
        for index, monster in enumerate(self.available_monsters.values()):
            selected = index == self.ui_indexes['switch']
            item_bg_rect = pygame.FRect((0, 0), (width, item_height)) \
                .move_to(midleft=(bg_rect.left, bg_rect.top + item_height / 2 + index * item_height + v_offset))

            # icon
            icon_surf = self.monster_frames['icons'][monster.name]
            icon_rect = icon_surf.get_frect(
                midleft=bg_rect.topleft + vector(self.window_width * 0.005,
                                                 item_height / 2 + index * item_height + v_offset))

            # name
            name_surf = self.fonts['regular'].render(f'{monster.name} ({monster.level})', False,
                                                     COLORS['white'] if selected else COLORS['black'])
            name_rect = name_surf.get_frect(
                topleft=(bg_rect.left + self.window_width * 0.05,
                         bg_rect.top + item_height / 3 + index * item_height + v_offset))

            # selection bg
            if selected:
                if item_bg_rect.collidepoint(bg_rect.topleft):
                    pygame.draw.rect(self.display_surface, COLORS['dark'], item_bg_rect, 0, 0, 5, 5)
                elif item_bg_rect.collidepoint(bg_rect.midbottom + vector(0, -1)):
                    pygame.draw.rect(self.display_surface, COLORS['dark'], item_bg_rect, 0, 0, 0, 0, 5, 5)
                else:
                    pygame.draw.rect(self.display_surface, COLORS['dark'], item_bg_rect)

            # draw
            if bg_rect.collidepoint(item_bg_rect.center):
                for surf, rect in ((icon_surf, icon_rect), (name_surf, name_rect)):
                    self.display_surface.blit(surf, rect)
                health_rect = pygame.FRect((name_rect.bottomleft + vector(0, 4), (100, 4)))
                energy_rect = pygame.FRect((health_rect.bottomleft + vector(0, 2), (100, 4)))
                draw_bar(
                    surf=self.display_surface,
                    rect=health_rect,
                    value=monster.health,
                    max_value=monster.get_stat('max_health'),
                    color=COLORS['red'],
                    bg_color=COLORS['black'],
                    radius=2
                )
                draw_bar(
                    surf=self.display_surface,
                    rect=energy_rect,
                    value=monster.energy,
                    max_value=monster.get_stat('max_energy'),
                    color=COLORS['blue'],
                    bg_color=COLORS['black'],
                    radius=2
                )

    def draw_text_field(self):
        # data
        width, height = self.window_width * 0.33, self.window_height * 0.15

        # bg
        bg_rect = pygame.FRect((self.window_width * 0.33, self.window_height * 0.8), (width, height))
        pygame.draw.rect(self.display_surface, COLORS['dark'], bg_rect, border_radius=12)
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect.inflate(-6, -6), border_radius=12)

    # battle system
    def check_active(self):
        if not self.turn:
            if self.turn_index < len(self.all_monsters):
                self.turn = True
                self.current_monster = self.all_monsters[self.turn_index]
                self.selected = False
                self.current_monster.monster.defending = False
                if self.current_monster in self.player_sprites:
                    self.selection_mode = 'general'
                else:
                    self.opponent_attack()
                    self.next_turn()
            else:
                if self.action_index == 0:
                    self.ui_indexes = {k: 0 for k in self.ui_indexes}
                    self.current_monster = None
                    self.selection_mode = None
                    self.selection_side = 'player'
                    self.selected_attack = None
                    self.executing_actions = True

                    self.execute_actions()

    def next_ability(self):
        self.ui_indexes = {k: 0 for k in self.ui_indexes}
        self.selection_mode = 'general'
        self.selected = False

    def next_turn(self):
        self.ui_indexes = {k: 0 for k in self.ui_indexes}
        self.current_monster.active = False
        self.current_monster = None
        self.turn_index += 1
        self.action_index = 0
        self.turn = False
        self.selection_mode = 'general'
        self.selected = False

    def execute_actions(self):
        self.player_sprites = pygame.sprite.Group(
            sorted(self.player_sprites.sprites(), key=lambda sprite: sprite.pos_index))
        self.opponent_sprites = pygame.sprite.Group(
            sorted(self.opponent_sprites.sprites(), key=lambda sprite: sprite.pos_index))
        if not self.timers['action'].active:
            if self.action_index < len(self.actions_list):
                self.timers['action'].activate()
                action = self.actions_list[self.action_index]
                if self.all_monsters[action['index']].alive and action['target'].alive:
                    match action['action']:
                        case 'activate_attack':
                            self.all_monsters[action['index']].activate_attack(action['target'],
                                                                               action['selected_attack'])
                        case 'switch_monster':
                            pass
                        case 'catch':
                            self.monster_data['player'].append(action['target'].monster)
                            self.player_monsters_ref[len(self.player_monsters_ref)] = action['target'].monster
                            action['target'].instant_kill(None)
                        case _:
                            debug(f'Something went wrong when attempting to execute action: {action["action"]}!')
                else:
                    self.timers['action'].deactivate()
                    self.action_index += 1
                    self.execute_actions()
                self.action_index += 1
            else:
                self.round_over()

    def round_over(self):
        self.timers['action'].deactivate()
        self.action_index = 0
        self.turn_index = 0
        self.turn = False
        self.executing_actions = False
        self.all_monsters = self.player_sprites.sprites() + self.opponent_sprites.sprites()
        self.all_monsters.sort(
            key=lambda monster_sprite: monster_sprite.monster.get_stat('speed'), reverse=True)
        for monster in self.all_monsters:
            monster.monster.energy = monster.monster.get_stat('max_energy')
        self.actions_list.clear()

    def apply_attack(self, target_sprite, attack, amount):
        # Play the attack animation
        AttackSprite(
            target_sprite.rect.center,
            self.monster_frames['attacks'][game_data.attack_data[attack]['animation']],
            self.battle_sprites
        )
        self.sounds['sfx_' + game_data.attack_data[attack]['animation']].play()

        # Get correct attack damage amount (defense, element)
        attack_element = game_data.attack_data[attack]['element']
        target_element = target_sprite.monster.element

        # Check for vulnerabilities
        if target_element in ELEMENT_RELATIONSHIPS.get(attack_element, {}).get('vulnerable_to', []):
            amount *= 2
        # Check for resistances
        if target_element in ELEMENT_RELATIONSHIPS.get(attack_element, {}).get('resistant_to', []):
            amount *= 0.5

        # get fraction of the damage by targets defense
        target_defense = 1 - target_sprite.monster.get_stat('defense') / 2000
        if target_sprite.monster.defending:
            target_defense -= 0.2
        target_defense = max(0, min(1, target_defense))

        # Apply the attack damage to the target
        target_sprite.monster.health -= int(amount * target_defense)
        self.check_death(target_sprite)

    def opponent_attack(self):
        ability = choice(self.current_monster.monster.get_abilities())
        random_target = choice(self.opponent_sprites.sprites()) if game_data.attack_data[ability]['side'] == 'player' \
            else choice(self.player_sprites.sprites())
        self.actions_list.append(
            {
                'index': self.turn_index,
                'action': 'activate_attack',
                'selected_attack': ability,
                'target': random_target
            }
        )

    def check_death(self, monster_sprite):
        if monster_sprite.monster.health <= 0:
            monster_sprite.alive = False
            self.apply_death(monster_sprite)

    def apply_death(self, monster_sprite):
        if not monster_sprite.alive:
            if self.player_sprites in monster_sprite.groups():  # player
                active_monsters = [active_monster_sprite.monster for
                                   active_monster_sprite in self.player_sprites.sprites()]
                available_monsters = [monster for monster in self.monster_data['player']
                                      if monster.health > 0 and monster not in active_monsters]
                if available_monsters:
                    new_monster_index = -1
                    for index, sprite in enumerate(self.player_sprites):
                        if sprite == monster_sprite:
                            new_monster_index = index
                    monster = available_monsters[0]
                    new_monster_data = (monster, new_monster_index, monster_sprite.pos_index, 'player')
                    print(new_monster_data)
                else:
                    new_monster_data = None
            else:  # enemy
                # replace with new if available
                new_monster_data = (self.monster_data['opponent'][0], monster_sprite.index,
                                    monster_sprite.pos_index, 'opponent') if self.monster_data['opponent'] else None
                if self.monster_data['opponent']:
                    self.monster_data['opponent'].pop(0)

                # xp
                defender_level = monster_sprite.monster.level
                for player_sprite in self.player_sprites:
                    attacker_level = player_sprite.monster.level
                    xp_amount = 50 * attacker_level * defender_level
                    player_sprite.monster.update_exp(xp_amount)

            # kill existing
            monster_sprite.instant_kill(new_monster_data)

    def check_end_battle(self):
        # player wins
        if len(self.opponent_sprites) == 0 and not self.battle_over:
            self.round_over()
            self.check_evolution()
            self.battle_over = True
            for monster in self.monster_data['player']:
                monster.energy = monster.get_stat('max_energy')
            self.end_battle(self.character)
        # opponent wins
        elif len(self.player_sprites) == 0 and not self.battle_over:
            self.battle_over = True
            pygame.quit()
            exit()

    # update
    def update(self, dt):
        # updates
        self.check_end_battle()
        if not self.battle_over:
            self.check_active()
            self.battle_sprites.update(dt)
            if not self.executing_actions:
                self.input()
            for timer in self.timers.values():
                timer.update()

        # drawing
        self.display_surface.blit(self.bg_surf, (0, 0))
        self.battle_sprites.draw_sprites(self.current_monster, self.selection_side, self.selection_mode,
                                         self.ui_indexes['target'], self.player_sprites, self.opponent_sprites)
        self.draw_ui()
        debug_str = ""
        if self.player_sprites:
            for monster in self.player_sprites:
                debug_str += str(monster)
        debug(debug_str)

        if self.draw_actions: self.draw_text_field()
