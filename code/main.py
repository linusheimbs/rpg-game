from settings import *
from random import randint, uniform

from support import *
from game_data import CHARACTER_DATA
from timer import Timer

from sprites import Sprite, AnimatedSprite, MonsterPatchSprite, BorderSprite, CollidableSprite, TransitionSprite
from entities import Player, Characters
from groups import AllSprites
from monster import Monster
from monster_inventory import MonsterInventory
from battle import Battle
from evolution import Evolution

from dialogue import DialogueTree

from debug import debug


class Game:
    # general setup
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Pykemon')
        self.clock = pygame.time.Clock()

        # player monsters
        self.player_monsters = {
            0: Monster('Plumette', 5),
            1: Monster('Sparchu', 5),
            2: Monster('Finsta', 5),
        }

        # groups
        self.collision_sprites = pygame.sprite.Group()
        self.all_sprites = AllSprites(self.collision_sprites)
        self.character_sprites = pygame.sprite.Group()
        self.transition_sprites = pygame.sprite.Group()
        self.encounter_sprites = pygame.sprite.Group()

        # transition / tint
        self.transition_target = None
        self.tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.tint_mode = 'untint'
        self.tint_progress = 0
        self.tint_direction = -1
        self.tint_speed = 600

        # setup
        self.import_assets()
        self.setup(self.tmx_maps[START_POS], 'start')
        self.audio['overworld'].play(loops=-1, fade_ms=1000)

        # overlays
        self.dialogue_tree = None
        self.monster_index = MonsterInventory(self.player_monsters, self.fonts, self.monster_frames)
        self.monster_index_open = False
        self.battle = None

        # encounter
        self.encounter_timer = Timer(250)
        self.spawn_chance = 90
        self.evolution = None
        self.evolution_queue = []

    def import_assets(self):
        self.tmx_maps = import_tmx_maps('..', 'data', 'maps')

        self.overworld_frames = {
            'water': import_folder('..', 'graphics', 'tilesets', 'water'),
            'coast': import_coastline(24, 12, '..', 'graphics', 'tilesets', 'coast'),
            'characters': import_all_characters('..', 'graphics', 'characters')
        }

        self.monster_frames = {
            'icons': import_folder_dict('..', 'graphics', 'icons'),
            'monsters': import_monster(4, 2, '..', 'graphics', 'monsters'),
            'attacks': import_attacks('..', 'graphics', 'attacks'),
            'ui': import_folder_dict('..', 'graphics', 'ui')
        }
        self.monster_frames['outlines'] = outline_creator(self.monster_frames['monsters'], 4)

        self.bg_frames = import_folder_dict('..', 'graphics', 'backgrounds')

        self.star_animation_frames = import_folder('..', 'graphics', 'other', 'star animation')

        self.fonts = {
            'dialogue': pygame.font.Font(join('..', 'graphics', 'fonts', 'PixeloidSans.ttf'), 30),
            'regular': pygame.font.Font(join('..', 'graphics', 'fonts', 'PixeloidSans.ttf'), 18),
            'small': pygame.font.Font(join('..', 'graphics', 'fonts', 'PixeloidSans.ttf'), 14),
            'bold': pygame.font.Font(join('..', 'graphics', 'fonts', 'dogicapixelbold.otf'), 20)
        }

        self.audio = audio_importer('..', 'audio')

    def setup(self, tmx_map, player_start_pos):
        # clear the map
        for group in (self.collision_sprites, self.all_sprites, self.character_sprites, self.transition_sprites):
            group.empty()

        # terrain
        for layer in ['Terrain', 'Terrain Top']:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, WORLD_LAYERS['bg'])

        # water
        for obj in tmx_map.get_layer_by_name('Water'):
            for x in range(int(obj.x), int(obj.x + obj.width), TILE_SIZE):
                for y in range(int(obj.y), int(obj.y + obj.height), TILE_SIZE):
                    AnimatedSprite((x, y), self.overworld_frames['water'], self.all_sprites, WORLD_LAYERS['water'])

        # coast
        for obj in tmx_map.get_layer_by_name('Coast'):
            terrain = obj.properties['terrain']
            side = obj.properties['side']
            AnimatedSprite((obj.x, obj.y), self.overworld_frames['coast'][terrain][side], self.all_sprites,
                           WORLD_LAYERS['bg'])

        # grass patches
        for obj in tmx_map.get_layer_by_name('Monsters'):
            MonsterPatchSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.encounter_sprites),
                               obj.properties['biome'], obj.properties['min_level'], obj.properties['max_level'],
                               obj.properties['monsters'])

        # collision objects
        for obj in tmx_map.get_layer_by_name('Collisions'):
            BorderSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        # objects
        for obj in tmx_map.get_layer_by_name('Objects'):
            if obj.name == 'top':
                Sprite((obj.x, obj.y), obj.image, self.all_sprites, WORLD_LAYERS['top'])
            else:
                CollidableSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        # transition objects
        for obj in tmx_map.get_layer_by_name('Transition'):
            TransitionSprite((obj.x, obj.y), (obj.width, obj.height), (obj.properties['target'], obj.properties['pos']),
                             self.transition_sprites)

        # entities
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                if obj.properties['pos'] == player_start_pos:
                    self.player = Player(
                        pos=(obj.x, obj.y),
                        frames=self.overworld_frames['characters']['player'],
                        groups=self.all_sprites,
                        facing_direction=obj.properties['direction'],
                        collision_sprites=self.collision_sprites
                    )
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name != 'Player':
                Characters(
                    pos=(obj.x, obj.y),
                    frames=self.overworld_frames['characters'][obj.properties['graphic']],
                    groups=(self.all_sprites, self.collision_sprites, self.character_sprites),
                    facing_direction=obj.properties['direction'],
                    character_data=CHARACTER_DATA[obj.properties['character_id']],
                    player=self.player,
                    create_dialogue=self.create_dialogue,
                    collision_sprites=self.collision_sprites,
                    radius=obj.properties['radius'],
                    nurse=obj.properties['character_id'] == 'Nurse',
                    sounds=self.audio
                )

    # dialogue system
    def input(self):
        if not self.dialogue_tree and not self.battle:
            keys = pygame.key.get_just_pressed()
            if (keys[pygame.K_f] and not self.player.blocked) or (keys[pygame.K_SPACE] and not self.player.blocked):
                for character in self.character_sprites:
                    if check_connection(TILE_SIZE * 2, self.player, character, 30):
                        self.player.block()
                        character.change_facing_direction(self.player.rect.center)
                        self.create_dialogue(character)
                        character.can_rotate = False
            if keys[pygame.K_TAB] or keys[pygame.K_i]:
                self.player.blocked = not self.player.blocked
                self.monster_index_open = not self.monster_index_open
            if keys[pygame.K_ESCAPE]:
                if self.monster_index_open:
                    self.player.unblock()
                    self.monster_index_open = False

    def create_dialogue(self, character):
        if not self.dialogue_tree:
            self.dialogue_tree = DialogueTree(character, self.player, self.all_sprites, self.fonts['dialogue'],
                                              self.end_dialogue)
            character.block()

    def end_dialogue(self, character):
        self.dialogue_tree = None
        if character.nurse:
            for monster in self.player_monsters.values():
                monster.health = monster.get_stat('max_health')
                monster.energy = monster.get_stat('max_energy')
            self.player.unblock()
        elif not character.character_data['defeated']:
            self.audio['overworld'].fadeout(1000)
            self.audio['battle'].play(loops=-1, fade_ms=4000)

            self.transition_target = Battle(
                player_monsters=self.player_monsters,
                opponent_monsters=character.monsters,
                monster_frames=self.monster_frames,
                bg_surf=self.bg_frames[character.character_data['biome']],
                fonts=self.fonts,
                end_battle=self.end_battle,
                character=character,
                check_evolution=self.check_evolution,
                sounds=self.audio
            )

            self.tint_mode = 'tint'
        elif not self.evolution:
            self.player.unblock()

    # battle encounters
    def check_for_monster(self):
        if [sprite for sprite in self.encounter_sprites if sprite.rect.colliderect(self.player.hitbox)]\
                and not self.battle and self.player.direction:
            if not self.encounter_timer.active:
                self.encounter_timer.activate()
                x = randint(0, 100)
                if x >= self.spawn_chance:
                    self.monster_encounter()
        else:
            self.encounter_timer.deactivate()

    def monster_encounter(self):
        sprites = [sprite for sprite in self.encounter_sprites if sprite.rect.colliderect(self.player.hitbox)]
        if sprites and self.player.direction:
            # block player
            self.player.block()

            # create encounters
            wild_monsters = {}
            amount = randint(1, 3)
            for i in range(amount):
                lvl = randint(sprites[0].min_lvl, sprites[0].max_lvl)
                monster_index = randint(0, len(sprites[0].monsters) - 1)
                new_monster = Monster(sprites[0].monsters[monster_index], lvl)
                wild_monsters[i] = new_monster

            self.audio['overworld'].fadeout(1000)
            self.audio['battle'].play(loops=-1, fade_ms=4000)

            # battle
            self.transition_target = Battle(
                player_monsters=self.player_monsters,
                opponent_monsters=wild_monsters,
                monster_frames=self.monster_frames,
                bg_surf=self.bg_frames[sprites[0].biome],
                fonts=self.fonts,
                end_battle=self.end_battle,
                character=None,
                check_evolution=self.check_evolution,
                sounds=self.audio
            )
            self.tint_mode = 'tint'

    def end_battle(self, character):
        self.audio['battle'].fadeout(1000)
        self.audio['overworld'].play(loops=-1, fade_ms=1000)

        self.transition_target = 'level'
        self.tint_mode = 'tint'
        if character:
            character.character_data['defeated'] = True
            self.create_dialogue(character)
        elif not self.evolution:

            self.player.unblock()

    # transition system
    def transition_check(self):
        sprites = [sprite for sprite in self.transition_sprites if sprite.rect.colliderect(self.player.hitbox)]
        if sprites:
            self.player.block()
            self.transition_target = sprites[0].target
            self.tint_mode = 'tint'

    def tint_screen(self, dt):
        if self.tint_mode == 'untint':
            self.tint_progress -= self.tint_speed * dt

        if self.tint_mode == 'tint':
            self.tint_progress += self.tint_speed * dt
            if self.tint_progress >= 255:
                if type(self.transition_target) == Battle:
                    self.battle = self.transition_target
                elif self.transition_target == 'level':
                    self.battle = None
                else:
                    self.setup(self.tmx_maps[self.transition_target[0]], self.transition_target[1])
                self.tint_mode = 'untint'
                self.transition_target = None

        self.tint_progress = max(0, min(self.tint_progress, 255))
        self.tint_surf.set_alpha(self.tint_progress)
        self.display_surface.blit(self.tint_surf, (0, 0))

    # evolutions
    def check_evolution(self):
        for index, monster in self.player_monsters.items():
            if monster.evolution:
                if monster.level >= monster.evolution[1]:
                    self.evolution_queue.append((index, monster))

            # Start the first evolution if any evolutions are queued
            if self.evolution_queue and not self.evolution:
                self.start_evolution()

    def start_evolution(self):
        if self.evolution_queue:
            index, monster = self.evolution_queue.pop(0)
            self.player.block()
            self.evolution = Evolution(
                frames=self.monster_frames['monsters'],
                start_monster=monster.name,
                end_monster=monster.evolution[0],
                font=self.fonts['bold'],
                end_evolution=self.end_evolution,
                star_frames=self.star_animation_frames
            )
            self.player_monsters[index] = Monster(monster.evolution[0], monster.level)

    def end_evolution(self):
        self.evolution = None
        if self.evolution_queue:
            self.start_evolution()
        else:
            if not self.dialogue_tree:
                self.player.unblock()

    # run function
    def run(self):
        while True:
            dt = self.clock.tick() / 1000
            self.display_surface.fill('black')

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # update
            self.encounter_timer.update()
            self.input()
            self.transition_check()
            self.all_sprites.update(dt)
            self.check_for_monster()

            # drawing
            self.all_sprites.draw(self.player)

            # overlays
            if self.dialogue_tree:          self.dialogue_tree.update(self.evolution)
            if self.monster_index_open:     self.monster_index.update(dt)
            if self.battle:                 self.battle.update(dt)
            if self.evolution:              self.evolution.update(dt)

            self.tint_screen(dt)

            # debug()

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
