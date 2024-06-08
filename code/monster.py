from game_data import MONSTER_DATA, ATTACK_DATA


class Monster:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.paused = True

        # stats
        self.element = MONSTER_DATA[name]['stats']['element']
        self.base_stats = MONSTER_DATA[name]['stats']
        self.health = self.base_stats['max_health'] * self.level
        self.energy = max(1, self.base_stats['max_energy'] * (self.level // 10))
        self.initiative = 0
        self.abilities = MONSTER_DATA[name]['abilities']
        self.defending = False

        # experience
        self.exp = 0
        self.level_up = self.level * self.level * 150
        self.evolution = MONSTER_DATA[self.name]['evolve']

    def reduce_energy(self, attack):
        self.energy -= ATTACK_DATA[attack]['cost']

    def stat_limiter(self):
        self.health = max(0, min(self.health, self.get_stat('max_health')))
        self.energy = max(0, min(self.energy, self.get_stat('max_energy')))

    def update_exp(self, amount):
        if self.level != 100:
            if self.level_up - self.exp > amount:
                self.exp += amount
            else:
                self.level += 1
                self.exp = amount - (self.level_up - self.exp)
                self.level_up = self.level * self.level * 150

    # getters
    def get_stat(self, stat):
        return self.base_stats[stat] * self.level if stat != 'max_energy'\
            else max(1, self.base_stats['max_energy'] * (self.level // 10))

    def get_stats(self):
        return {
            'health': self.get_stat('max_health'),
            'energy': self.get_stat('max_energy'),
            'attack': self.get_stat('attack'),
            'defense': self.get_stat('defense'),
            'speed': self.get_stat('speed'),
            'recovery': self.get_stat('recovery')
        }

    def get_base_damage(self, attack):
        return self.get_stat('attack') * ATTACK_DATA[attack]['amount']

    def get_abilities(self, all_abilities=True):
        if all_abilities:
            return [ability for lvl, ability in self.abilities.items() if self.level >= lvl]
        else:
            return [ability for lvl, ability in self.abilities.items() if self.level >= lvl]

    def get_info(self):
        return (
            (self.health, self.get_stat('max_health')),
            (self.energy, self.get_stat('max_energy')),
            (self.initiative, 100)
        )

    def update(self, dt):
        self.stat_limiter()
        if not self.paused:
            self.initiative += self.get_stat('speed') * dt
