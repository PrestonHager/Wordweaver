# wordweaver_project.py

import logging

from os.path import exists

from ipapy.ipachar import IPAChar
from ipapy import IPA_TO_UNICODE, UNICODE_TO_IPA

class WordweaverProject:
    def __init__(self, name: str, file: str=None, pulmonic_inventory: list[IPAChar] | list[str]=[], non_pulmonic_inventory: list[IPAChar] | list[str]=[], vowel_inventory: list[IPAChar] | list[str]=[], lexicon: dict[str, str]={}):
        """
        Initialize a new WordweaverProject object.

        The inventories should be a list of IPAChar objects or unicode strings of each phoneme.

        :param name: str: The name of the project.
        :param file: str: The file path to save the project to can be a relative or absolute path.
        :param pulmonic_inventory: list[IPAChar] | list[str]: A list of pulmonic consonants.
        :param non_pulmonic_inventory: list[IPAChar] | list[str]: A list of non-pulmonic consonants.
        :param vowel_inventory: list[IPAChar] | list[str]: A list of vowels.
        :param lexicon: dict[str, str]: A dictionary of words.
        :raises ValueError: If the inventory is not a list of IPAChar objects or unicode strings. Each lists must contain only one type.
        """
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.name = name
        self.file = file
        self._pulmonic_inventory = pulmonic_inventory
        self._non_pulmonic_inventory = non_pulmonic_inventory
        self._vowel_inventory = vowel_inventory
        self._lexicon = lexicon
        # Convert strings to Phoneme objects
        if all(isinstance(sound, str) for sound in pulmonic_inventory):
            self._pulmonic_inventory = self._inventory_to_ipa(pulmonic_inventory)
        elif not all(isinstance(sound, IPAChar) for sound in pulmonic_inventory):
            raise ValueError("Invalid pulmonic inventory; values must be of type str or IPAChar")
        if all(isinstance(sound, str) for sound in non_pulmonic_inventory):
            self._non_pulmonic_inventory = self._inventory_to_ipa(non_pulmonic_inventory)
        elif not all(isinstance(sound, IPAChar) for sound in non_pulmonic_inventory):
            raise ValueError("Invalid non-pulmonic inventory; values must be of type str or IPAChar")
        if all(isinstance(sound, str) for sound in vowel_inventory):
            self._vowel_inventory = self._inventory_to_ipa(vowel_inventory)
        elif not all(isinstance(sound, IPAChar) for sound in vowel_inventory):
            raise ValueError("Invalid vowel inventory; values must be of type str or IPAChar")

    def _inventory_to_ipa(self, inv: list[str]) -> list[IPAChar]:
        ipa_inv = []
        for sound in inv:
            try:
                ipa_inv.append(UNICODE_TO_IPA[sound])
            except KeyError:
                self.logger.warning(f"Invalid IPA character: {sound}")
        return ipa_inv

    @property
    def pulmonic_inventory(self) -> list[IPAChar]:
        return self._pulmonic_inventory

    @pulmonic_inventory.setter
    def pulmonic_inventory(self, value: list[IPAChar] | list[str]):
        if all(isinstance(sound, str) for sound in value):
            self._pulmonic_inventory = self._inventory_to_ipa(value)
        elif not all(isinstance(sound, IPAChar) for sound in value):
            raise ValueError("Invalid pulmonic inventory; values must be of type IPAChar or str")
        else:
            self._pulmonic_inventory = value

    @property
    def non_pulmonic_inventory(self) -> list[IPAChar]:
        return self._non_pulmonic_inventory

    @non_pulmonic_inventory.setter
    def non_pulmonic_inventory(self, value: list[IPAChar] | list[str]):
        if all(isinstance(sound, str) for sound in value):
            self._non_pulmonic_inventory = self._inventory_to_ipa(value)
        elif not all(isinstance(sound, IPAChar) for sound in value):
            raise ValueError("Invalid non-pulmonic inventory; values must be of type IPAChar or str")
        else:
            self._non_pulmonic_inventory = value

    @property
    def vowel_inventory(self) -> list[IPAChar]:
        return self._vowel_inventory

    @vowel_inventory.setter
    def vowel_inventory(self, value: list[IPAChar] | list[str]):
        if all(isinstance(sound, str) for sound in value):
            self._vowel_inventory = self._inventory_to_ipa(value)
        elif not all(isinstance(sound, IPAChar) for sound in value):
            raise ValueError("Invalid vowel inventory; values must be of type IPAChar or str")
        else:
            self._vowel_inventory = value

    @property
    def inventory(self) -> dict[str, IPAChar]:
        return {
            "pulmonic": self.pulmonic_inventory,
            "non_pulmonic": self.non_pulmonic_inventory,
            "vowel": self.vowel_inventory,
        }

    @property
    def lexicon(self) -> dict[str, str]:
        return self._lexicon

    @lexicon.setter
    def lexicon(self, value: dict[str, str]):
        self._lexicon = value

    def save(self) -> bool:
        """Save the project to the file specified in the project.

        .. code-block::
        
            File format is as follows:
            Magic number:         4 bytes     0x87AFFA87
            Version:              1 byte      0x01
            Name length:          2 bytes     len(name)
            Name:                 n bytes     name
            Pulmonic length:      1 bytes     len(pulmonic_inventory)
            Pulmonics:            n bytes     pulmonic_inventory
            Non-pulmonic length:  1 bytes     len(non_pulmonic_inventory)
            Non-pulmonics:        n bytes     non_pulmonic_inventory
            Vowel length:         1 bytes     len(vowel_inventory)
            Vowels:               n bytes     vowel_inventory
            Lexicon length:       3 bytes     len(lexicon)
            Lexicon:
                Word length:      1 byte      len(word)
                Word:             n bytes     word

        Given the format. There is a maximum length of
        65535 characters for the name; 255 for the
        phonology_inventory, and vowel_inventory.
        The lexicon is limited to 16777215 words. With
        each word limited to 255 characters.
        """
        if self.file is None:
            return False
        with open(self.file, 'wb') as f_out:
            f_out.write(0x87AFFA87.to_bytes(4, 'big'))
            f_out.write(0x01.to_bytes(1, 'big'))
            f_out.write(len(self.name).to_bytes(2, 'big'))
            f_out.write(self.name.encode())
            self._write_inventory(f_out, self.pulmonic_inventory)
            self._write_inventory(f_out, self.non_pulmonic_inventory)
            self._write_inventory(f_out, self.vowel_inventory)
            f_out.write(len(self.lexicon).to_bytes(3, 'big'))
            for word in self.lexicon:
                f_out.write(len(word).to_bytes(1, 'big'))
                f_out.write(word.encode())
        return True

    @staticmethod
    def _write_inventory(f_stream, inventory: list[IPAChar]):
        f_stream.write(len(inventory).to_bytes(1, 'big'))
        for sound in inventory:
            sound_unicode = sound.unicode_repr if sound.unicode_repr is not None else IPA_TO_UNICODE[sound.canonical_representation]
            f_stream.write(len(sound_unicode.encode()).to_bytes(1, 'big'))
            f_stream.write(sound_unicode.encode())

    @staticmethod
    def from_file(file):
        # Check that the file exists
        if not exists(file):
            raise FileNotFoundError(f"File not found: {file}")
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
            pulmonic_inventory = WordweaverProject._read_inventory(f_in)
            non_pulmonic_inventory = WordweaverProject._read_inventory(f_in)
            vowel_inventory = WordweaverProject._read_inventory(f_in)
            lexicon_length = int.from_bytes(f_in.read(3), 'big')
            lexicon = {}
            # TODO: format lexicon
            for _ in range(lexicon_length):
                lexicon.append(f_in.read(1).decode())
        return WordweaverProject(name, file, pulmonic_inventory, non_pulmonic_inventory, vowel_inventory, lexicon)

    @staticmethod
    def _read_inventory(f_stream):
        inventory = []
        inventory_len = int.from_bytes(f_stream.read(1), 'big')
        for _ in range(inventory_len):
            sound_len = int.from_bytes(f_stream.read(1), 'big')
            sound_unicode = f_stream.read(sound_len).decode()
            inventory.append(UNICODE_TO_IPA[sound_unicode])
        return inventory
