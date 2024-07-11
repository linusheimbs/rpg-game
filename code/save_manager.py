import os
import json
from settings import *
from debug import debug


class SaveManager:
    def __init__(self, filename=f"savefile{VERSION}.json", filepath='../save_data/saves/'):
        self.filepath = filepath
        self.filename = filename
        self.ensure_directory_exists()

    def ensure_directory_exists(self):
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

    def get_full_path(self):
        return os.path.join(self.filepath, self.filename)

    def save(self, data, file_name=f"savefile{VERSION}.json"):
        self.filename = file_name
        full_path = self.get_full_path()
        try:
            with open(full_path, 'w') as savefile:
                json.dump(data, savefile, indent=4)
            debug(f"Game saved to {full_path}")
        except IOError as e:
            debug(f"An error occurred while saving the game: {e}")

    def load(self, file_name=f"savefile{VERSION}.json"):
        self.filename = file_name
        full_path = self.get_full_path()
        if not os.path.exists(full_path):
            debug(f"No save file found: {full_path}")
            return None

        try:
            with open(full_path, 'r') as savefile:
                data = json.load(savefile)
                debug(f"Game loaded from {full_path}")
                return data
        except IOError as e:
            debug(f"An error occurred while loading the game: {e}")
            return None
        except json.JSONDecodeError as e:
            debug(f"Error decoding JSON data from the save file: {e}")
            return None


save_manager = SaveManager()
