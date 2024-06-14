import json

class DataGetter:

    @staticmethod
    def phrases_reader(path_to_phrases: str):
        phrases = []
        with open(path_to_phrases, 'r', encoding='utf-8') as phrases_file:
            phrases = [phrase.replace('\n', '') for phrase in phrases_file.readlines()]
        return phrases


    @staticmethod
    def targets_reader(path_to_targets : str):
        targets = {}
        with open(path_to_targets, 'r', encoding='utf-8') as targets_file:
            targets = json.load(targets_file)
        return targets