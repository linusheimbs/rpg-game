from settings import *
from config_manager import config_manager
from sprites import MonsterSprite, MonsterNameSprite, MonsterLevelSprite, MonsterStatsSprite, MonsterOutlineSprite, \
    AttackSprite, TimedSprite
from groups import BattleSprites
from game_data import ATTACK_DATA
from support import draw_bar
from timer import Timer
from random import choice


class Battle:
    # main
    def __init__(self, player_monsters, opponent_monsters, monster_frames, bg_surf, fonts, end_battle, character,
                 check_evolution, sounds):
        # general
        self.display_surface = pygame.display.get_surface()
        self.monster_data = {
            'player': player_monsters,
            'opponent': opponent_monsters
        }
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
                'top': (0.25 * self.window_width, 0.27 * self.window_height),
                'center': (0.17 * self.window_width, 0.54 * self.window_height),
                'bottom': (0.30 * self.window_width, 0.80 * self.window_height)
            },
            'right': {
                'top': (0.75 * self.window_width, 0.27 * self.window_height),
                'center': (0.85 * self.window_width, 0.55 * self.window_height),
                'bottom': (0.78 * self.window_width, 0.82 * self.window_height)
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
            for index, monster in {k: v for k, v in monsters.items() if k <= 2}.items():
                self.create_monster(monster, index, index, entity)

            # remove opponent monster data
            for i in range(len(self.opponent_sprites)):
                del self.monster_data['opponent'][i]

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
                if self.selection_mode == 'target':
                    sprite_group = self.opponent_sprites if self.selection_side == 'opponent' else self.player_sprites
                    sprites = {sprite.pos_index: sprite for sprite in sprite_group}
                    monster_sprite = sprites[list(sprites.keys())[self.ui_indexes['target']]]

                    if self.selected_attack:
                        if self.current_monster.monster.energy >= ATTACK_DATA[self.selected_attack]['cost']:
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
                # attack
                elif self.selection_mode == 'attacks':
                    self.selection_mode = 'target'
                    self.selected_attack = self.current_monster.monster.get_abilities(
                        all_abilities=False)[self.ui_indexes['attacks']]
                    self.selection_side = ATTACK_DATA[self.selected_attack]['side']
                    self.ui_indexes = {k: 0 for k in self.ui_indexes}
                # defend
                elif self.selection_mode == 'defend':
                    if self.ui_indexes['defend'] == 0:
                        if self.current_monster.monster.energy > 0:
                            self.actions_list.append(
                                {
                                    'index': self.turn_index,
                                    'action': 'set_defend'
                                }
                            )
                            self.current_monster.monster.energy -= 1
                            if self.current_monster.monster.energy <= 0:
                                self.selected = True
                                self.next_turn()
                            else:
                                self.selection_mode = 'general'
                        else:
                            TimedSprite(self.current_monster.rect.center, self.monster_frames['ui']['cross'],
                                        self.battle_sprites, 1000)
                    if self.ui_indexes['defend'] == 1:
                        self.selection_mode = 'general'
                # switch
                elif self.selection_mode == 'switch':
                    if self.available_monsters.items():
                        self.selected = True
                        self.actions_list.append(
                            {
                                'index': self.turn_index,
                                'action': 'switch_monster',
                                'new_monster': list(self.available_monsters.items())[self.ui_indexes['switch']]
                            }
                        )
                        self.next_turn()
                    else:
                        self.selection_mode = 'general'
                # general
                elif self.selection_mode == 'general':
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
            if self.selection_mode == 'general':
                self.draw_general()
            if self.selection_mode == 'attacks':
                self.draw_attacks()
            if self.selection_mode == 'defend':
                self.draw_defend()
            if self.selection_mode == 'switch':
                self.draw_switch()

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
                element = ATTACK_DATA[ability]['element']
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
        active_monsters = [(monster_sprite.index, monster_sprite.monster) for monster_sprite in self.player_sprites]
        self.available_monsters = {index: monster for index, monster in self.monster_data['player'].items()
                                   if (index, monster) not in active_monsters and monster.health > 0}
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

    # battle system
    def check_active(self):
        if not self.turn:
            if self.turn_index < len(self.player_sprites.sprites() + self.opponent_sprites.sprites()):
                self.turn = True
                self.all_monsters = self.player_sprites.sprites() + self.opponent_sprites.sprites()
                self.all_monsters.sort(
                    key=lambda monster_sprite: monster_sprite.monster.get_stat('speed'), reverse=True)
                self.current_monster = self.all_monsters[self.turn_index]
                self.selected = False
                self.current_monster.monster.defending = False
                self.current_monster.monster.energy = self.current_monster.monster.get_stat('max_energy')
                self.current_monster.active = True
                if self.player_sprites in self.current_monster.groups():
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

    def next_turn(self):
        self.ui_indexes = {k: 0 for k in self.ui_indexes}
        self.current_monster.active = False
        self.turn_index += 1
        self.turn = False

    def execute_actions(self):
        if not self.timers['action'].active:
            if self.action_index < len(self.actions_list):
                self.timers['action'].activate()
                action = self.actions_list[self.action_index]
                if self.all_monsters[action['index']].alive:
                    if action['action'] == 'activate_attack':
                        self.all_monsters[action['index']].activate_attack(action['target'], action['selected_attack'])
                    elif action['action'] == 'switch_monster':
                        self.all_monsters[action['index']].kill()
                        self.create_monster(action['new_monster'][1], action['new_monster'][0],
                                            self.all_monsters[action['index']].pos_index, 'player')
                    elif action['action'] == 'set_defend':
                        self.all_monsters[action['index']].defending = True
                    elif action['action'] == 'catch':
                        self.monster_data['player'][len(self.monster_data['player'])] = action['target'].monster
                        action['target'].instant_kill(None)
                else:
                    self.timers['action'].deactivate()
                    self.action_index += 1
                    self.execute_actions()
                self.action_index += 1
            else:
                self.round_over()

    def round_over(self):
        self.apply_death()
        self.actions_list.clear()
        self.action_index = 0
        self.turn_index = 0
        self.turn = False
        self.executing_actions = False

    def apply_attack(self, target_sprite, attack, amount):
        # Play the attack animation
        AttackSprite(target_sprite.rect.center, self.monster_frames['attacks'][ATTACK_DATA[attack]['animation']],
                     self.battle_sprites)
        self.sounds['sfx_' + ATTACK_DATA[attack]['animation']].play()

        # Get correct attack damage amount (defense, element)
        attack_element = ATTACK_DATA[attack]['element']
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
        target_sprite.monster.health -= amount * target_defense
        self.check_death()

    def opponent_attack(self):
        ability = choice(self.current_monster.monster.get_abilities())
        random_target = choice(self.opponent_sprites.sprites()) if ATTACK_DATA[ability]['side'] == 'player' \
            else choice(self.player_sprites.sprites())
        self.actions_list.append(
            {
                'index': self.turn_index,
                'action': 'activate_attack',
                'selected_attack': ability,
                'target': random_target
            }
        )

    def check_death(self):
        for monster_sprite in self.opponent_sprites.sprites() + self.player_sprites.sprites():
            if monster_sprite.monster.health <= 0:
                monster_sprite.alive = False

    def apply_death(self):
        for monster_sprite in self.opponent_sprites.sprites() + self.player_sprites.sprites():
            if not monster_sprite.alive:
                if self.player_sprites in monster_sprite.groups():  # player
                    active_monsters = [(active_monster_sprite.index, active_monster_sprite.monster) for
                                       active_monster_sprite in self.player_sprites.sprites()]
                    available_monsters = [(index, monster) for index, monster in self.monster_data['player'].items()
                                          if monster.health > 0 and (index, monster) not in active_monsters]
                    if available_monsters:
                        new_monster_data = [(monster, index, monster_sprite.pos_index, 'player')
                                            for index, monster in available_monsters][0]
                    else:
                        new_monster_data = None
                else:
                    # replace with new if available
                    new_monster_data = (list(self.monster_data['opponent'].values())[0], monster_sprite.index,
                                        monster_sprite.pos_index, 'opponent') if self.monster_data['opponent'] else None
                    if self.monster_data['opponent']:
                        del self.monster_data['opponent'][min(self.monster_data['opponent'])]

                    # xp
                    xp_amount = monster_sprite.monster.level * 150 / len(self.player_sprites)
                    for player_sprite in self.player_sprites:
                        player_sprite.monster.update_exp(xp_amount)

                # kill existing
                monster_sprite.instant_kill(new_monster_data)

    def check_end_battle(self):
        # player wins
        if len(self.opponent_sprites) == 0 and not self.battle_over:
            self.round_over()
            self.check_evolution()
            self.battle_over = True
            for monster in self.monster_data['player'].values():
                monster.energy = monster.get_stat('max_energy')
            self.end_battle(self.character)
        # opponent wins
        if len(self.player_sprites) == 0 and not self.battle_over:
            self.battle_over = True
            pygame.quit()
            exit()

    # update
    def update(self, dt):
        # updates
        self.check_end_battle()
        if not self.battle_over:
            self.battle_sprites.update(dt)
            self.check_active()
            if not self.executing_actions:
                self.input()
            for timer in self.timers.values():
                timer.update()

        # drawing
        self.display_surface.blit(self.bg_surf, (0, 0))
        self.battle_sprites.draw_sprites(self.current_monster, self.selection_side, self.selection_mode,
                                         self.ui_indexes['target'], self.player_sprites, self.opponent_sprites)
        self.draw_ui()
