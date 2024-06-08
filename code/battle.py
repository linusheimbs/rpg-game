from settings import *
from sprites import MonsterSprite, MonsterNameSprite, MonsterLevelSprite, MonsterStatsSprite, MonsterOutlineSprite,\
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
        self.bg_surf = pygame.transform.scale(bg_surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.fonts = fonts
        self.battle_over = False
        self.end_battle = end_battle
        self.character = character
        self.check_evolution = check_evolution

        # groups
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()

        # control
        self.selected = False
        self.current_monster = None
        self.selection_mode = None
        self.selection_side = 'player'
        self.selected_attack = None
        self.indexes = {
            'general': 0,
            'monster': 0,
            'attacks': 0,
            'defend': 0,
            'switch': 0,
            'target': 0
        }

        self.timers = {
            'opponent delay': Timer(1000, func=self.opponent_attack)
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
            pos = list(BATTLE_POSITIONS['left'].values())[pos_index]
            groups = (self.battle_sprites, self.player_sprites)
            frames = {state: [pygame.transform.flip(frame, True, False)
                              for frame in frames] for state, frames in frames.items()}
            outline_frames = {state: [pygame.transform.flip(frame, True, False)
                              for frame in frames] for state, frames in outline_frames.items()}
        else:
            pos = list(BATTLE_POSITIONS['right'].values())[pos_index]
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
                case 'general': limiter = len(BATTLE_CHOICES['full'])
                case 'attacks': limiter = len(self.current_monster.monster.get_abilities())
                case 'target': limiter = len(self.opponent_sprites) if self.selection_side == 'opponent'\
                    else len(self.player_sprites)
                case 'defend': limiter = 2
                case 'switch': limiter = len(self.available_monsters)
                case _: limiter = 1

            if limiter > 0:
                # up
                if keys[pygame.K_w]:
                    self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] - 1) % limiter
                # down
                if keys[pygame.K_s]:
                    self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] + 1) % limiter

            # confirm
            if keys[pygame.K_f] or keys[pygame.K_SPACE]:
                # target
                if self.selection_mode == 'target':
                    sprite_group = self.opponent_sprites if self.selection_side == 'opponent' else self.player_sprites
                    sprites = {sprite.pos_index: sprite for sprite in sprite_group}
                    monster_sprite = sprites[list(sprites.keys())[self.indexes['target']]]

                    if self.selected_attack:
                        if self.current_monster.monster.energy >= ATTACK_DATA[self.selected_attack]['cost']:
                            self.selected = True
                            self.current_monster.activate_attack(monster_sprite, self.selected_attack)
                        else:
                            TimedSprite(self.current_monster.rect.center, self.monster_frames['ui']['cross'],
                                        self.battle_sprites, 1000)
                    else:
                        if monster_sprite.monster.health < monster_sprite.monster.get_stat('max_health') * 0.9:
                            self.selected = True
                            self.monster_data['player'][len(self.monster_data['player'])] = monster_sprite.monster
                            monster_sprite.delayed_kill(None)
                            self.resume()
                        else:
                            TimedSprite(monster_sprite.rect.center, self.monster_frames['ui']['cross'],
                                        self.battle_sprites, 1000)
                # attack
                elif self.selection_mode == 'attacks':
                    self.selection_mode = 'target'
                    self.selected_attack = self.current_monster.monster.get_abilities(
                        all_abilities=False)[self.indexes['attacks']]
                    self.selection_side = ATTACK_DATA[self.selected_attack]['side']
                    self.indexes = {k: 0 for k in self.indexes}
                # defend
                elif self.selection_mode == 'defend':
                    if self.indexes['defend'] == 0:
                        self.selected = True
                        self.current_monster.defending = True
                        self.resume()
                    if self.indexes['defend'] == 1:
                        self.selection_mode = 'general'
                # switch
                elif self.selection_mode == 'switch':
                    self.selected = True
                    index, new_monster = list(self.available_monsters.items())[self.indexes['switch']]
                    self.current_monster.kill()
                    self.create_monster(new_monster, index, self.current_monster.pos_index, 'player')
                    self.selection_mode = None
                    self.resume()
                # general
                elif self.selection_mode == 'general':
                    if self.indexes['general'] == 0:
                        self.selection_mode = 'attacks'
                    if self.indexes['general'] == 1:
                        self.selection_mode = 'defend'
                    if self.indexes['general'] == 2:
                        self.selection_mode = 'switch'
                    if self.indexes['general'] == 3:
                        self.selection_mode = 'target'
                        self.selection_side = 'opponent'

            # going back
            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ('attacks', 'switch', 'defend'):
                    self.selection_mode = 'general'
                    for item in self.indexes:
                        if item != 'general':
                            self.indexes[item] = 0
                elif self.selection_mode == 'target':
                    self.selection_mode = 'general'
                    self.selection_side = 'player'
                    self.selected_attack = None
                    for item in self.indexes:
                        if item != 'general':
                            self.indexes[item] = 0

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
        for index, (option, data_dict) in enumerate(BATTLE_CHOICES['full'].items()):
            if index == self.indexes['general']:
                surf = self.monster_frames['ui'][data_dict['icon']]
            else:
                surf = pygame.transform.grayscale(self.monster_frames['ui'][data_dict['icon']])
            rect = surf.get_frect(center=self.current_monster.rect.midright + data_dict['pos'])
            self.display_surface.blit(surf, rect)

    def draw_attacks(self):
        # data
        abilities = self.current_monster.monster.get_abilities(all_abilities=False)
        width, height = WINDOW_WIDTH * 0.1, WINDOW_HEIGHT * 0.2
        visible_attacks = 6
        item_height = height / visible_attacks

        # bg
        bg_rect = pygame.FRect((0, 0), (width, height)).move_to(
            midleft=self.current_monster.rect.midright + vector(WINDOW_WIDTH * 0.023, 0))
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        # fg
        for index, ability in enumerate(abilities):
            selected = index == self.indexes['attacks']
            # text
            if selected:
                element = ATTACK_DATA[ability]['element']
                text_color = COLORS[element]
            else:
                text_color = COLORS['black']
            text_surf = self.fonts['regular'].render(ability, False, text_color)
            # rect
            text_rect = text_surf.get_frect(
                center=bg_rect.midtop + vector(0, item_height/2 + index * item_height))
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
        width, height = WINDOW_WIDTH * 0.1, WINDOW_HEIGHT * 0.1
        item_height = height / 2

        # bg
        bg_rect = pygame.FRect((0, 0), (width, height))\
            .move_to(midleft=self.current_monster.rect.midright + vector(WINDOW_WIDTH * 0.023, 0))
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        # fg
        for index, text in enumerate(['Confirm', 'Back']):
            selected = index == self.indexes['defend']
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
        width, height = WINDOW_WIDTH * 0.25, WINDOW_HEIGHT * 0.35
        visible_monsters = 4
        item_height = height / visible_monsters
        v_offset = 0 if self.indexes['switch'] < visible_monsters else\
            -(self.indexes['switch'] - visible_monsters + 1) * item_height

        # bg
        bg_rect = pygame.FRect((0, 0), (width, height)).move_to(
            midleft=self.current_monster.rect.midright + vector(WINDOW_WIDTH * 0.023, 0))
        pygame.draw.rect(self.display_surface, COLORS['light'], bg_rect, 0, 5)

        # monsters
        active_monsters = [(monster_sprite.index, monster_sprite.monster) for monster_sprite in self.player_sprites]
        self.available_monsters = {index: monster for index, monster in self.monster_data['player'].items()
                                   if (index, monster) not in active_monsters and monster.health > 0}
        for index, monster in enumerate(self.available_monsters.values()):
            selected = index == self.indexes['switch']
            item_bg_rect = pygame.FRect((0, 0), (width, item_height))\
                .move_to(midleft=(bg_rect.left, bg_rect.top + item_height/2 + index * item_height + v_offset))

            # icon
            icon_surf = self.monster_frames['icons'][monster.name]
            icon_rect = icon_surf.get_frect(
                midleft=bg_rect.topleft + vector(WINDOW_WIDTH * 0.005, item_height/2 + index * item_height + v_offset))

            # name
            name_surf = self.fonts['regular'].render(f'{monster.name} ({monster.level})', False,
                                                     COLORS['white']if selected else COLORS['black'])
            name_rect = name_surf.get_frect(
                topleft=(bg_rect.left + WINDOW_WIDTH * 0.05,
                         bg_rect.top + item_height/3 + index * item_height + v_offset))

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
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if monster_sprite.monster.initiative >= 100:
                self.selected = False
                monster_sprite.monster.defending = False
                monster_sprite.monster.energy = monster_sprite.monster.get_stat('max_energy')
                self.update_all_monsters('pause')
                monster_sprite.monster.initiative = 0
                monster_sprite.set_highlight(True)
                self.current_monster = monster_sprite
                if self.player_sprites in monster_sprite.groups():
                    self.selection_mode = 'general'
                else:
                    self.timers['opponent delay'].activate()

    def update_all_monsters(self, option):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            monster_sprite.monster.paused = True if option == 'pause' else False

    def apply_attack(self, target_sprite, attack, amount):
        # Play the attack animation
        AttackSprite(target_sprite.rect.center, self.monster_frames['attacks'][ATTACK_DATA[attack]['animation']],
                     self.battle_sprites)
        self.sounds[ATTACK_DATA[attack]['animation']].play()

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

        # resume
        self.resume()

    def opponent_attack(self):
        ability = choice(self.current_monster.monster.get_abilities())
        random_target = choice(self.opponent_sprites.sprites()) if ATTACK_DATA[ability]['side'] == 'player'\
            else choice(self.player_sprites.sprites())
        self.current_monster.activate_attack(random_target, ability)

    def check_death(self):
        for monster_sprite in self.opponent_sprites.sprites() + self.player_sprites.sprites():
            if monster_sprite.monster.health <= 0:
                if self.player_sprites in monster_sprite.groups():  # player
                    active_monsters = [(active_monster_sprite.index, active_monster_sprite.monster) for
                                       active_monster_sprite in self.player_sprites.sprites()]
                    available_monsters = [(index, monster) for index, monster in self.monster_data['player'].items()
                                          if monster.health > 0 and (index, monster) not in active_monsters]
                    if available_monsters:
                        new_monster_data = [(monster, index, monster_sprite.pos_index, 'player')
                                            for index, monster in available_monsters][0]
                    else: new_monster_data = None
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
                monster_sprite.delayed_kill(new_monster_data)

    def resume(self):
        self.update_all_monsters('resume')
        self.indexes = {k: 0 for k in self.indexes}
        self.current_monster = None
        self.selection_mode = None
        self.selection_side = 'player'
        self.selected_attack = None

    def check_end_battle(self):
        # player wins
        if len(self.opponent_sprites) == 0 and not self.battle_over:
            self.check_evolution()
            self.battle_over = True
            self.update_all_monsters('pause')
            for monster in self.monster_data['player'].values():
                monster.initiative = 0
                monster.energy = monster.get_stat('max_energy')
            self.end_battle(self.character)
        # opponent wins
        if len(self.player_sprites) == 0 and not self.battle_over:
            self.battle_over = True
            self.update_all_monsters('pause')
            pygame.quit()
            exit()

    # update
    def update(self, dt):
        # updates
        self.check_end_battle()
        self.input()
        for timer in self.timers.values():
            timer.update()
        self.battle_sprites.update(dt)
        self.check_active()

        # drawing
        self.display_surface.blit(self.bg_surf, (0, 0,))
        self.battle_sprites.draw_sprites(self.current_monster, self.selection_side, self.selection_mode,
                                         self.indexes['target'], self.player_sprites, self.opponent_sprites)
        self.draw_ui()
