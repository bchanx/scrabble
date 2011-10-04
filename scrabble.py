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
		allwords = open(dictionary_file).read().split()
		self.dictionary = set(w for w in allwords if len(w) >= 2)

		# initialize board rules
		config = ConfigParser.ConfigParser()
		config.read(config_file)
		self.board_size = config.getint('init', 'board_size')
		self.rack_size = config.getint('init', 'rack_size')
		self.player_size = config.getint('init', 'player_size')
		self.double_letter = config.get('init', 'double_letter').split('/')
		self.triple_letter = config.get('init', 'triple_letter').split('/')
		self.double_word = config.get('init', 'double_word').split('/')
		self.triple_word = config.get('init', 'triple_letter').split('/')

		# initialize letters
		self.letters = {}
		self.letters_remaining = 0
		for l in letters:
			count, points = config.get('letters', l).split('/')
			self.letters[l] = {}
			self.letters[l]['count'] = int(count)
			self.letters[l]['points'] = int(points)
			self.letters_remaining += int(count)

		# initialize current words in play
		self.words_in_play = {}
		self.tiles_in_play = {}
		words_in_play = config.get('init', 'words_in_play')
		if words_in_play:
			words_and_position = words_in_play.split('/')
			for words in words_and_position:
				word, tile, direction = words.split(';')
				self.words_in_play[word] = {}
				self.words_in_play[word]['tile'] = tile
				self.words_in_play[word]['direction'] = direction
				self._updateLettersInPlay(word, tile, direction)

		# initialize current tiles in hand for players
		self.letters_in_hand = {}
		for player_no in range(0, self.player_size):
			player = 'player'+str(player_no)
			init_letters = config.get('letters_in_hand', player)
			if init_letters:
				self.letters_in_hand[player] = init_letters.split('/')
			else:
				self.letters_in_hand[player] = []
				random.seed()
				while (len(self.letters_in_hand[player]) < self.rack_size) and (self.letters_remaining > 0):
					l = letters[random.randint(0, len(letters)-1)]
					if self.letters[l]['count'] > 0:
						self.letters_in_hand[player].append(l)
						self.letters[l]['count'] -= 1
						self.letters_remaining -= 1


	# update self.tiles_in_play with letters in 'word'
	def _updateLettersInPlay(self, word, tile, direction):
		cur_tile = tile
		for letter in word:
			# already in map, update direction
			if cur_tile in self.tiles_in_play:
				self.tiles_in_play[cur_tile][direction] = word
			else:	
				self.tiles_in_play[cur_tile] = {}
				self.tiles_in_play[cur_tile]['letter'] = letter
				if direction == 'across':
					self.tiles_in_play[cur_tile]['across'] = word
					self.tiles_in_play[cur_tile]['down'] = None
				else:
					self.tiles_in_play[cur_tile]['across'] = None
					self.tiles_in_play[cur_tile]['down'] = word
				self.tiles_in_play[cur_tile]['points'] = self.letters[letter]['points']
			#remove from global letters and update tile position
			self.letters[letter]['count'] -= 1
			self.letters_remaining -= 1
			cur_tile= self._updatePosition(cur_tile, direction)


	# update to next tile according to direction
	def _updatePosition(self, tile, direction):
		if direction == 'across':
			row, col = tile.split('-')
			return str(row) + '-' + str(int(col)+1)
		else:
			row, col = tile.split('-')
			return str(int(row)+1) + '-' + str(col)
		

	# find best possible word player can create on a tile
	def _findMostPoints(self, letters_in_hand, tile):
		return (None, None, None, None)


	# get next optimal move
	def findOptimal(self, player):
		bestMove = False
		for tile in self.tiles_in_play:
			if not (self.tiles_in_play[tile]['across'] and self.tiles_in_play[tile]['down']):
				#sys.stderr.write("i am tile: " + str(tile) + ' and my letter is: ' + str(self.tiles_in_play[tile]['letter'])+'\n')
				(word, tile, direction, points) = self._findMostPoints(self.letters_in_hand[player], self.tiles_in_play[tile])

		return


	# prettify current scrabble board and output
	def printBoard(self):
		for row in range(0, self.board_size):
			output = '|'
			for col in range(0, self.board_size):
				tile = str(row) + '-' + str(col)
				if tile in self.tiles_in_play:
					output = output + self.tiles_in_play[tile]['letter'] + ' |'
				else:
					output = output + '__|'
			print output
		return


	# output current letters in hand
	def printLetters(self, player):
		print player + ': ' + str(self.letters_in_hand[player])


if __name__ == '__main__':
	scrabble = Scrabble()
	scrabble.printBoard()
	scrabble.printLetters('player0')
	scrabble.findOptimal('player0')
