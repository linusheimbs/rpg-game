from settings import *
from config_manager import config_manager
from support import check_connection
from timer import Timer
from random import choice
from monster import Monster


class Entity(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, facing_direction):
        super().__init__(groups)
        self.z = WORLD_LAYERS['main']

        # graphics
        self.frame_index, self.frames = 0, frames
        self.facing_direction = facing_direction

        # movement
        self.direction = vector()
        self.speed = 250
        self.blocked = False
        self.animation_speed = ANIMATION_SPEED

        # sprite setup
        self.image = self.frames[self.get_state()][self.frame_index]
        self.rect = self.image.get_frect(center=pos)
        self.hitbox = self.rect.inflate(-self.rect.width/1.5, -self.rect.height/1.5)
        self.hitbox_offset_y = self.rect.height/2.5
        self.y_sort = self.rect.centery
        self.hitbox.centery = self.rect.centery + self.hitbox_offset_y

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.frame_index %= len(self.frames[self.get_state()])
        self.image = self.frames[self.get_state()][int(self.frame_index)]

    def get_state(self):
        moving = bool(self.direction)
        if moving:
            if self.direction.x != 0:
                self.facing_direction = 'right' if self.direction.x > 0 else 'left'
            else:
                self.facing_direction = 'down' if self.direction.y > 0 else 'up'
        return f'{self.facing_direction}{"" if moving else "_idle"}'

    def change_facing_direction(self, target_pos):
        relation = vector(target_pos) - vector(self.rect.center)
        if abs(relation.y) < 40:
            self.facing_direction = 'right' if relation.x > 0 else 'left'
        else:
            self.facing_direction = 'down' if relation.y > 0 else 'up'

    def block(self):
        self.blocked = True
        self.direction = vector(0, 0)

    def unblock(self):
        self.blocked = False


class Player(Entity):
    def __init__(self, pos, frames, groups, facing_direction, collision_sprites):
        super().__init__(pos, frames, groups, facing_direction)
        self.collision_sprites = collision_sprites
        self.noticed = False

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = vector()
        if keys[config_manager.settings['controls']['up'][0]]\
                or keys[config_manager.settings['controls']['up'][1]]:
            input_vector.y -= 1
        if keys[config_manager.settings['controls']['down'][0]]\
                or keys[config_manager.settings['controls']['down'][1]]:
            input_vector.y += 1
        if keys[config_manager.settings['controls']['left'][0]]\
                or keys[config_manager.settings['controls']['left'][1]]:
            input_vector.x -= 1
        if keys[config_manager.settings['controls']['right'][0]]\
                or keys[config_manager.settings['controls']['right'][1]]:
            input_vector.x += 1
        if keys[pygame.K_LSHIFT]:
            self.speed = 250 * 1.6
            self.animation_speed = ANIMATION_SPEED * 1.8
        else:
            self.speed = 250
            self.animation_speed = ANIMATION_SPEED
        self.direction = input_vector

    def move(self, dt):
        # normalize the vector
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # Save current positions for potential rollback
        initial_centerx = self.rect.centerx
        initial_centery = self.rect.centery

        # horizontal movement
        self.rect.centerx += self.direction.x * self.speed * dt
        self.hitbox.centerx = self.rect.centerx
        if self.check_collision('horizontal'):
            self.rect.centerx = initial_centerx
            self.hitbox.centerx = initial_centerx

        # vertical movement
        self.rect.centery += self.direction.y * self.speed * dt
        self.hitbox.centery = self.rect.centery + self.hitbox_offset_y
        if self.check_collision('vertical'):
            self.rect.centery = initial_centery
            self.hitbox.centery = initial_centery + self.hitbox_offset_y

        self.y_sort = self.rect.centery

    def check_collision(self, axis):
        collided = False
        for sprite in self.collision_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                collided = True
                if axis == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.hitbox.left
                    elif self.direction.x < 0:
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                elif axis == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.direction.y < 0:
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery
        return collided

    def to_dict(self):
        return {
            'pos': (self.rect.centerx, self.rect.centery),
            'facing_direction': self.facing_direction,
            'speed': self.speed,
            'animation_speed': self.animation_speed,
            'noticed': self.noticed
        }

    def from_dict(self, data):
        self.rect.center = data['pos']
        self.hitbox.center = self.rect.center + vector(0, self.hitbox_offset_y)
        self.hitbox.center = self.rect.center
        self.facing_direction = data['facing_direction']
        self.speed = data['speed']
        self.animation_speed = data['animation_speed']
        self.noticed = data['noticed']

    def update(self, dt):
        if not self.blocked:
            self.input()
            self.move(dt)
        self.animate(dt)


class Characters(Entity):
    def __init__(self, pos, frames, groups, facing_direction, character_data, player, create_dialogue,
                 collision_sprites, radius, char_id, sounds):
        super().__init__(pos, frames, groups, facing_direction)
        self.character_data = character_data
        self.player = player
        self.create_dialogue = create_dialogue
        self.collision_rects = [sprite.rect for sprite in collision_sprites if sprite is not self]
        self.char_id = char_id
        self.monsters = {i: Monster(name, lvl) for i, (name, lvl) in character_data['monsters'].items()}\
            if 'monsters' in character_data else None

        # movement
        self.has_moved = False
        self.can_rotate = True
        self.has_noticed = False
        self.radius = int(radius)
        self.view_directions = character_data['directions']

        # idle
        self.timers = {
            'look around': Timer(1500, autostart=True, repeat=True, func=self.random_view_direction),
            'notice': Timer(1000, func=self.start_move)
        }

        # sound
        self.sounds = sounds

    def get_dialogue(self):
        return self.character_data['dialogue'][f"{'defeated' if self.character_data['defeated'] else 'default'}"]

    def random_view_direction(self):
        if self.can_rotate:
            self.facing_direction = choice(self.view_directions)

    def raycast(self):
        if check_connection(self.radius, self, self.player) and self.has_los() and not self.has_moved\
                and not self.has_noticed and not self.character_data['defeated']:
            self.player.block()
            self.player.change_facing_direction(self.rect.center)
            self.timers['notice'].activate()
            self.can_rotate = False
            self.has_noticed = True
            self.player.noticed = True
            self.sounds['sfx_notice'].play()

    def has_los(self):
        if vector(self.rect.center).distance_to(self.player.rect.center) < self.radius:
            collisions = [bool(rect.clipline(self.rect.center, self.player.rect.center)) for rect in
                          self.collision_rects]
            return not any(collisions)

    def start_move(self):
        relation = (vector(self.player.rect.center) - vector(self.rect.center)).normalize()
        self.direction = vector(round(relation.x), round(relation.y))

    def move(self, dt):
        if not self.has_moved and self.direction:
            if not self.hitbox.inflate(10, 10).colliderect(self.player.hitbox):
                self.rect.center += self.direction * self.speed * dt
                self.hitbox.center = self.rect.center + vector(0, self.hitbox_offset_y)
            else:
                self.direction = vector()
                self.has_moved = True
                self.create_dialogue(self)
                self.player.noticed = False

    def to_dict(self):
        return {
            'pos': (self.rect.centerx, self.rect.centery),
            'facing_direction': self.facing_direction,
            'character_data': self.character_data,
            'has_moved': self.has_moved,
            'can_rotate': self.can_rotate,
            'has_noticed': self.has_noticed,
            'radius': self.radius,
            'view_directions': self.view_directions,
        }

    def from_dict(self, data):
        self.rect.center = data['pos']
        self.hitbox.center = self.rect.center + vector(0, self.hitbox_offset_y)
        self.facing_direction = data['facing_direction']

        # Convert character_data keys to integers
        self.character_data = data['character_data']
        if 'monsters' in self.character_data:
            self.character_data['monsters'] = {int(k): v for k, v in self.character_data['monsters'].items()}
            self.monsters = {i: Monster(name, lvl) for i, (name, lvl) in self.character_data['monsters'].items()}\
                if 'monsters' in self.character_data else None

        self.has_moved = data['has_moved']
        self.can_rotate = data['can_rotate']
        self.has_noticed = data['has_noticed']
        self.radius = data['radius']
        self.view_directions = data['view_directions']

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()
        self.animate(dt)
        if self.character_data['look_around'] and not self.character_data['defeated'] and not self.blocked:
            self.raycast()
            self.move(dt)
