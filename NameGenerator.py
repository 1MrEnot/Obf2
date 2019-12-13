from typing import Dict, Optional


class NameGenerator:

    def __init__(self):

        self.names: Dict[str, str] = dict()
        self.prefix: str = 'O'
        self.changers = ('O', '0')

    def is_obfuscated(self, old_name: str) -> bool:

        for symbol in self.changers:
            old_name = old_name.replace(symbol, '')

        return not bool(old_name)

    def get_name(self, old_name: str) -> Optional[str]:

        if old_name is None or old_name == '':
            return

        if self.is_obfuscated(old_name):
            return old_name

        if old_name in self.names:
            return self.names[old_name]

        new_name = bin(len(self.names))[2:]
        for num, el in enumerate(self.changers):
            new_name = new_name.replace(str(num), el)

        new_name = self.prefix + new_name

        self.names[old_name] = new_name

        return new_name

    def get_existing_name(self, old_name: str) -> Optional[str]:

        if old_name in self.names:
            return self.get_name(old_name)

    def in_dictionary(self, old_name: str) -> bool:
        return old_name in self.names
