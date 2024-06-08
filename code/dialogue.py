from settings import *
from timer import Timer


class DialogueTree:
    def __init__(self, character, player, all_sprites, font, end_dialogue):
        self.character = character
        self.player = player
        self.all_sprites = all_sprites
        self.font = font
        self.end_dialogue = end_dialogue

        self.dialogue = character.get_dialogue()
        self.dialogue_num = len(self.dialogue)
        self.dialogue_index = 0

        self.current_dialogue = DialogueSprite(
            message=self.dialogue[self.dialogue_index],
            character=self.character,
            groups=self.all_sprites,
            font=self.font
        )
        self.dialogue_timer = Timer(250, autostart=True)

    def input(self):
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_f] and not self.dialogue_timer.active or\
                keys[pygame.K_SPACE] and not self.dialogue_timer.active:
            self.current_dialogue.kill()
            self.dialogue_index += 1
            if self.dialogue_index < self.dialogue_num:
                self.current_dialogue = DialogueSprite(
                    message=self.dialogue[self.dialogue_index],
                    character=self.character,
                    groups=self.all_sprites,
                    font=self.font
                )
                self.dialogue_timer.activate()
            else:
                self.end_dialogue(self.character)

    def update(self, evolution):
        if not evolution:
            self.dialogue_timer.update()
            self.input()


class DialogueSprite(pygame.sprite.Sprite):
    def __init__(self, message, character, groups, font):
        super().__init__(groups)
        self.z = WORLD_LAYERS['top']

        # text
        text_surf = font.render(message, False, COLORS['black'])
        padding = 10
        width = max(30, text_surf.get_width() + padding * 2)
        height = text_surf.get_height() + padding * 2

        # background
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, COLORS['pure white'], surf.get_frect(topleft=(0, 0)), 0, 4)
        pygame.draw.rect(surf, COLORS['blue'], surf.get_frect(topleft=(0, 0)), 4, 4)
        surf.blit(text_surf, text_surf.get_frect(center=(width/2, height/2)))

        self.image = surf
        self.rect = self.image.get_frect(midbottom=character.rect.midtop + vector(0, -10))
