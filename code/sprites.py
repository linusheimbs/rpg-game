import pygame.sprite

from settings import *
from config_manager import config_manager
from random import uniform
from support import draw_bar
from timer import Timer


# overworld sprites
class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=WORLD_LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.z = z
        self.y_sort = self.rect.centery
        self.hitbox = self.rect.copy()


class BorderSprite(Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy()


class TransitionSprite(Sprite):
    def __init__(self, pos, size, target, groups):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.target = target


class CollidableSprite(Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.inflate(-self.rect.width * 0.1, -self.rect.height * 0.5)
        self.hitbox_offset_y = self.rect.height
        self.hitbox.centery = self.rect.centery + self.hitbox_offset_y / 4


class MonsterPatchSprite(Sprite):
    def __init__(self, pos, surf, groups, biome, min_lvl, max_lvl, names):
        super().__init__(pos, surf, groups, WORLD_LAYERS['main' if biome != 'sand' else 'bg'])
        self.y_sort = self.rect.centery - 32
        self.biome = biome
        self.min_lvl = min_lvl
        self.max_lvl = max_lvl
        self.monsters = names.split(',')


class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups, z=WORLD_LAYERS['main']):
        self.frame_index, self.frames = 0, frames
        super().__init__(pos, self.frames[self.frame_index], groups, z)

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


# battle sprites
class MonsterSprite(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, monster, index, pos_index, entity, apply_attack, create_monster):
        # data
        self.index = index
        self.pos_index = pos_index
        self.entity = entity
        self.monster = monster
        self.frame_index, self.frames, self.state = 0, frames, 'idle'
        self.animation_speed = ANIMATION_SPEED + uniform(-1, 1)
        self.z = BATTLE_LAYERS['monster']
        self.hightlight = False
        self.target_sprite = None
        self.current_attack = None
        self.apply_attack = apply_attack
        self.next_monster_data = None
        self.create_monster = create_monster
        self.alive = True

        # sprite setup
        super().__init__(groups)
        for state, surface_list in self.frames.items():
            new_surf_list = []
            width = config_manager.settings['video']['window_width'] // 10
            height = width
            for surf in surface_list:
                scaled_surf = pygame.transform.scale(surf, (width, height))
                new_surf_list.append(scaled_surf)
            self.frames[state] = new_surf_list
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(center=pos)

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.state == 'attack' and self.frame_index >= len(self.frames['attack']):
            # apply attack
            self.apply_attack(self.target_sprite, self.current_attack, self.monster.get_base_damage(
                self.current_attack))
            self.state = 'idle'
        self.frame_index %= len(self.frames[self.state])
        if self.hightlight:
            white_surf = pygame.mask.from_surface(self.image).to_surface()
            white_surf.set_alpha(0)
            self.image = white_surf
        else:
            self.image = self.frames[self.state][int(self.frame_index)]

    def activate_attack(self, target_sprite, attack):
        self.state = 'attack'
        self.frame_index = 0
        self.target_sprite = target_sprite
        self.current_attack = attack
        self.monster.reduce_energy(attack)

    def instant_kill(self, new_monster):
        self.next_monster_data = new_monster
        self.destroy()

    def destroy(self):
        if self.next_monster_data:
            self.create_monster(*self.next_monster_data)
        self.kill()

    def __repr__(self):
        return f"{self.monster.name} at lvl: {self.monster.level}"

    def update(self, dt):
        self.animate(dt)
        self.monster.update()


class MonsterOutlineSprite(pygame.sprite.Sprite):
    def __init__(self, monster_sprite, groups, frames):
        super().__init__(groups)
        self.z = BATTLE_LAYERS['outline']
        self.monster_sprite = monster_sprite
        self.frames = frames
        for state, surface_list in self.frames.items():
            new_surf_list = []
            width = config_manager.settings['video']['window_width'] // 10
            height = width
            for surf in surface_list:
                scaled_surf = pygame.transform.scale(surf, (width, height))
                new_surf_list.append(scaled_surf)
            self.frames[state] = new_surf_list

        self.image = self.frames[self.monster_sprite.state][self.monster_sprite.frame_index]
        self.rect = self.image.get_frect(center=self.monster_sprite.rect.center)

    def update(self, _):
        self.image = self.frames[self.monster_sprite.state][int(self.monster_sprite.frame_index)]

        if not self.monster_sprite.groups():
            self.kill()


class MonsterNameSprite(pygame.sprite.Sprite):
    def __init__(self, pos, monster_sprite, groups, font):
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        self.z = BATTLE_LAYERS['name']

        text_surf = font.render(monster_sprite.monster.name, False, COLORS['black'])
        padding = 5

        self.image = pygame.Surface((text_surf.get_width() + padding * 2, text_surf.get_height() + padding * 2),
                                    pygame.SRCALPHA)
        self.image.blit(text_surf, (padding, padding))
        self.rect = self.image.get_rect(midtop=pos)

    def update(self, _):
        if not self.monster_sprite.groups():
            self.kill()


class MonsterLevelSprite(pygame.sprite.Sprite):
    def __init__(self, entity, anchor, monster_sprite, groups, font):
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        self.font = font
        self.z = BATTLE_LAYERS['name']

        self.image = pygame.Surface((60, 26), pygame.SRCALPHA)
        self.rect = self.image.get_frect(topleft=anchor) if entity == 'player' \
            else self.image.get_frect(topright=anchor)
        self.xp_rect = pygame.FRect(0, self.rect.height - 2, self.rect.width, 2)

    def update(self, _):
        self.image.fill(pygame.Color(0, 0, 0, 0))

        text_surf = self.font.render(f'lvl: {self.monster_sprite.monster.level}', False, COLORS['black'])
        text_rect = text_surf.get_frect(center=(self.rect.width / 2, self.rect.height / 2))
        self.image.blit(text_surf, text_rect)

        draw_bar(
            surf=self.image,
            rect=self.xp_rect,
            value=self.monster_sprite.monster.exp,
            max_value=self.monster_sprite.monster.level_up,
            color=COLORS['black'],
            bg_color=pygame.Color(0, 0, 0, 0),
            radius=0
        )

        if not self.monster_sprite.groups():
            self.kill()


class MonsterStatsSprite(pygame.sprite.Sprite):
    def __init__(self, pos, monster_sprite, size, groups, font):
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        self.font = font
        self.z = BATTLE_LAYERS['overlay']

        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.rect = self.image.get_frect(midbottom=pos)

    def update(self, _):
        self.image.fill(pygame.Color(0, 0, 0, 0))

        for index, (value, max_value) in enumerate(self.monster_sprite.monster.get_info()):
            color = (COLORS['red'], COLORS['blue'], COLORS['gray'])[index]
            if index < 2:
                text_surf = self.font.render(f'{int(value)}/{max_value}', False, COLORS['black'])
                text_rect = text_surf.get_frect(topleft=(self.rect.width * 0.05, index * self.rect.height / 2))
                bar_rect = pygame.FRect(text_rect.bottomleft + vector(0, -self.rect.height * 0.05),
                                        (self.rect.width * 0.9, 4))
                self.image.blit(text_surf, text_rect)
                draw_bar(
                    surf=self.image,
                    rect=bar_rect,
                    value=value,
                    max_value=max_value,
                    color=color,
                    bg_color=COLORS['black'],
                    radius=2
                )
            else:
                init_rect = pygame.FRect((0, self.rect.height - 2), (self.rect.width, 2))
                draw_bar(
                    surf=self.image,
                    rect=init_rect,
                    value=value,
                    max_value=max_value,
                    color=color,
                    bg_color=COLORS['light'],
                    radius=0
                )

        if not self.monster_sprite.groups():
            self.kill()


class AttackSprite(AnimatedSprite):
    def __init__(self, pos, frames, groups):
        super().__init__(pos, frames, groups, BATTLE_LAYERS['overlay'])
        self.rect.center = pos

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

    def update(self, dt):
        self.animate(dt)


class TimedSprite(Sprite):
    def __init__(self, pos, surf, groups, duration):
        super().__init__(pos, surf, groups, z=BATTLE_LAYERS['overlay'])
        self.rect.center = pos
        self.death_timer = Timer(duration, autostart=True, func=self.kill)

    def update(self, _):
        self.death_timer.update()
