# wordweaver_project.py

from phonology import Phoneme, PhonemeType
from phonology_const import PULMONIC_CONSONANTS_LOOKUP_REVERSE, NON_PULMONIC_CONSONANTS_LOOKUP_REVERSE, VOWELS_LOOKUP_REVERSE

class WordweaverProject:
    def __init__(self, name: str, file: str=None, pulmonic_inventory: list[Phoneme] | list[str]=[], non_pulmonic_inventory: list[Phoneme] | list[str]=[], vowel_inventory: list[Phoneme] | list[str]=[], lexicon: list[str]=[]):
        self.name = name
        self.file = file
        self._pulmonic_inventory = pulmonic_inventory
        self._non_pulmonic_inventory = non_pulmonic_inventory
        self._vowel_inventory = vowel_inventory
        self._lexicon = lexicon
        # Convert strings to Phoneme objects
        if all(isinstance(sound, str) for sound in pulmonic_inventory):
            self._pulmonic_inventory = [Phoneme(sound, PhonemeType.PULMONIC_CONSONANT) for sound in pulmonic_inventory]
        elif not all(isinstance(sound, Phoneme) for sound in pulmonic_inventory):
            raise ValueError("Invalid pulmonic inventory; values must be of type str or Phoneme")
        if all(isinstance(sound, str) for sound in non_pulmonic_inventory):
            self._non_pulmonic_inventory = [Phoneme(sound, PhonemeType.NON_PULMONIC_CONSONANT) for sound in non_pulmonic_inventory]
        elif not all(isinstance(sound, Phoneme) for sound in non_pulmonic_inventory):
            raise ValueError("Invalid non-pulmonic inventory; values must be of type str or Phoneme")
        if all(isinstance(sound, str) for sound in vowel_inventory):
            self._vowel_inventory = [Phoneme(sound, PhonemeType.VOWEL) for sound in vowel_inventory]
        elif not all(isinstance(sound, Phoneme) for sound in vowel_inventory):
            raise ValueError("Invalid vowel inventory; values must be of type str or Phoneme")
    
    @property
    def pulmonic_inventory(self) -> list[Phoneme]:
        return self._pulmonic_inventory
    
    @pulmonic_inventory.setter
    def pulmonic_inventory(self, value: list[Phoneme]):
        if all(isinstance(sound, str) for sound in value):
            self._pulmonic_inventory = [Phoneme(sound, PhonemeType.PULMONIC_CONSONANT) for sound in value]
        elif not all(isinstance(sound, Phoneme) for sound in value):
            raise ValueError("Invalid pulmonic inventory; values must be of type Phoneme")
        else:
            self._pulmonic_inventory = value
    
    @property
    def non_pulmonic_inventory(self) -> list[Phoneme]:
        return self._non_pulmonic_inventory
    
    @non_pulmonic_inventory.setter
    def non_pulmonic_inventory(self, value: list[Phoneme]):
        if all(isinstance(sound, str) for sound in value):
            self._non_pulmonic_inventory = [Phoneme(sound, PhonemeType.NON_PULMONIC_CONSONANT) for sound in value]
        elif not all(isinstance(sound, Phoneme) for sound in value):
            raise ValueError("Invalid non-pulmonic inventory; values must be of type Phoneme")
        else:
            self._non_pulmonic_inventory = value
    
    @property
    def vowel_inventory(self) -> list[Phoneme]:
        return self._vowel_inventory
    
    @vowel_inventory.setter
    def vowel_inventory(self, value: list[Phoneme]):
        if all(isinstance(sound, str) for sound in value):
            self._vowel_inventory = [Phoneme(sound, PhonemeType.VOWEL) for sound in value]
        elif not all(isinstance(sound, Phoneme) for sound in value):
            raise ValueError("Invalid vowel inventory; values must be of type Phoneme")
        else:
            self._vowel_inventory = value
    
    @property
    def lexicon(self) -> list[str]:
        return self._lexicon
    
    @lexicon.setter
    def lexicon(self, value: list[str]):
        self._lexicon = value

    def save(self) -> bool:
        if self.file is None:
            return False
        # File format is as follows:
        # Magic number:     4 bytes     0x87AFFA87
        # Version:          1 byte      0x01
        # Name length:      2 bytes     len(name)
        # Name:             n bytes     name
        # Pulmonic length:  1 bytes     len(pulmonic_inventory)
        # Pulmonics:        n bytes     pulmonic_inventory
        # Non-pulmonic length: 1 bytes  len(non_pulmonic_inventory)
        # Non-pulmonics:    n bytes     non_pulmonic_inventory
        # Vowel length:     1 bytes     len(vowel_inventory)
        # Vowels:           n bytes     vowel_inventory
        # Lexicon length:   3 bytes     len(lexicon)
        # Lexicon:
        #   Word length:    1 byte      len(word)
        #   Word:           n bytes     word
        #
        # Given the format. There is a maximum length of
        # 65535 characters for the name; 255 for the 
        # phonology_inventory, and vowel_inventory.
        # The lexicon is limited to 16777215 words. With
        # each word limited to 255 characters.
        with open(self.file, 'wb') as f_out:
            f_out.write(0x87AFFA87.to_bytes(4, 'big'))
            f_out.write(0x01.to_bytes(1, 'big'))
            f_out.write(len(self.name).to_bytes(2, 'big'))
            f_out.write(self.name.encode())
            f_out.write(len(self.pulmonic_inventory).to_bytes(1, 'big'))
            for sound in self.pulmonic_inventory:
                f_out.write(sound.encode().rjust(4, b'\x00'))
            f_out.write(len(self.non_pulmonic_inventory).to_bytes(1, 'big'))
            for sound in self.non_pulmonic_inventory:
                f_out.write(sound.encode().rjust(4, b'\x00'))
            f_out.write(len(self.vowel_inventory).to_bytes(1, 'big'))
            for sound in self.vowel_inventory:
                f_out.write(sound.encode().rjust(4, b'\x00'))
            f_out.write(len(self.lexicon).to_bytes(3, 'big'))
            for word in self.lexicon:
                f_out.write(len(word).to_bytes(1, 'big'))
                f_out.write(word.encode())
        return True
    
    @staticmethod
    def from_file(file):
        # File format is the same as the save method
        # If the version is lower than the current version,
        # special handling is required.
        with open(file, 'rb') as f_in:
            magic_number = int.from_bytes(f_in.read(4), 'big')
            if magic_number != 0x87AFFA87:
                return None
            version = int.from_bytes(f_in.read(1), 'big')
            if version != 0x01:
                # TODO: Handle older versions
                # As a fallback, return None
                return None
            name_length = int.from_bytes(f_in.read(2), 'big')
            name = f_in.read(name_length).decode()
            pulmonic_inventory = []
            non_pulmonic_inventory = []
            vowel_inventory = []
            pulmonic_inventory_len = int.from_bytes(f_in.read(1), 'big')
            for i in range(pulmonic_inventory_len):
                sound = f_in.read(4).decode().lstrip('\x00')
                sound_ascii = PULMONIC_CONSONANTS_LOOKUP_REVERSE[sound]
                pulmonic_inventory.append(Phoneme(sound_ascii, PhonemeType.PULMONIC_CONSONANT))
            non_pulmonic_inventory_len = int.from_bytes(f_in.read(1), 'big')
            for i in range(non_pulmonic_inventory_len):
                sound = f_in.read(4).decode().lstrip('\x00')
                sound_ascii = NON_PULMONIC_CONSONANTS_LOOKUP_REVERSE[sound]
                non_pulmonic_inventory.append(Phoneme(sound_ascii, PhonemeType.NON_PULMONIC_CONSONANT))
            vowel_length_len = int.from_bytes(f_in.read(1), 'big')
            for i in range(vowel_length_len):
                sound = f_in.read(4).decode().lstrip('\x00')
                sound_ascii = VOWELS_LOOKUP_REVERSE[sound]
                vowel_inventory.append(Phoneme(sound_ascii, PhonemeType.VOWEL))
            lexicon_length = int.from_bytes(f_in.read(3), 'big')
            lexicon = []
            for i in range(lexicon_length):
                lexicon.append(f_in.read(1).decode())
        return WordweaverProject(name, file, pulmonic_inventory, non_pulmonic_inventory, vowel_inventory, lexicon)
