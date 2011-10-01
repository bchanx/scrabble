import os
import sys
import shutil
import random
import ConfigParser

config_dir = './config'
config_file = os.path.join(config_dir, 'scrabble.conf')
dictionary_file = os.path.join(config_dir, 'basic_english_word_list')
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'blank']

class Scrabble:

	def __init__(self):
		# initialize word list
		self.dictionary = []
		with open(dictionary_file, 'r') as f:
			for line in f:
				word = line.strip()
				if len(word) < 2:
					self.dictionary.append(word)

		config = ConfigParser.ConfigParser()
		config.read(config_file)

		# initialize board rules
		self.board_size = config.getint('rules', 'board_size')
		self.rack_size = config.getint('rules', 'rack_size')
		self.double_letter = config.get('rules', 'double_letter').split(';')
		self.triple_letter = config.get('rules', 'triple_letter').split(';')
		self.double_word = config.get('rules', 'double_word').split(';')
		self.triple_word = config.get('rules', 'triple_letter').split(';')

		# initialize letters rules
		self.letters = {}
		self.letters_remaining = 0
		for l in letters:
			count, points = config.get('letters', l).split(';')
			self.letters[l] = {}
			self.letters[l]['count'] = int(count)
			self.letters[l]['points'] = int(points)
			self.letters_remaining += int(count)

		# initialize current words in play
		self.words_in_play = {}

		# initialize current tiles in hand
		self.letters_in_hand = {}
		random.seed()
		letters_drawn = 0
		while (letters_drawn < self.rack_size) and (self.letters_remaining > 0):
			l = letters[random.randint(0, len(letters)-1)]
			if self.letters[l]['count'] > 0:
				if l not in self.letters_in_hand:
					self.letters_in_hand[l] = 1
				else:
					self.letters_in_hand[l] += 1
				letters_drawn += 1
				self.letters[l]['count'] -= 1
				self.letters_remaining -= 1


if __name__ == '__main__':
	scrabble = Scrabble()
