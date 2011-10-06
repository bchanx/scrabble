import os
import sys
import shutil
import random
import ConfigParser

config_dir = './config'
config_file = os.path.join(config_dir, 'scrabble.conf')
dictionary_file = os.path.join(config_dir, 'basic_english_word_list')
global_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'blank']

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
		for l in global_letters:
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
					l = letters[random.randint(0, len(global_letters)-1)]
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
				self.tiles_in_play[cur_tile]['start'] = tile
			# update tile position
			cur_tile = self._getPosition(cur_tile, 1, direction)


	# Returns new position if successful, False if outside board size.
	def _getPosition(self, tile, length, direction):
		if direction == 'across':
			row, col = tile.split('-')
			new_col = int(col) + length
			if new_col < 0 or new_col >= self.board_size:
				return False
			return str(row) + '-' + str(new_col)
		else:
			row, col = tile.split('-')
			new_row = int(row) + length
			if new_row < 0 or new_row >= self.board_size:
				return False
			return str(new_row) + '-' + str(col)
		


	# find all possible words creatable with player tiles and a pivot (SLOW)
	def _findPossibleWords(self, letters_in_hand, pivot):
		possible_words = []
		letters_in_hand.append(pivot)
		for word in self.dictionary:
			if pivot in word:
				if len(letters_in_hand) < len(word):
					continue
				validWord = True
				tmpletters = list(letters_in_hand)
				for l in word:
					if not word.count(l) <= tmpletters.count(l):
						# check blanks
						if 'blank' in tmpletters:
							if (word.count(l) - tmpletters.count(l)) <= tmpletters.count('blank'):
								for i in range(0, word.count(l) - tmpletters.count(l)):
									tmpletters.remove('blank')
									tmpletters.append(l)
								continue
						# not possible
						validWord = False
						break
				if validWord:
					possible_words.append(word)
		return possible_words


	# check whether word is valid
	def _checkWord(self, word):
		return word in self.dictionary


	# check whether words can be placed on the board
	def _checkWordPlacement(self, list_of_words, tile):
		# TODO: case if board is entirely empty
		valid_words = []
		pivot = self.tiles_in_play[tile]['letter']
		if not self.tiles_in_play[tile]['across']:
			direction = 'across'
			other_direction = 'down'
		else:
			direction = 'down'
			other_direction = 'across'

		for word in list_of_words:
			# find position of each pivot in the word
			start_pos = 0
			end_pos = len(word)
			for i in range(0, word.count(pivot)):
				validWord = True
				index = word.find(pivot, start_pos, end_pos)
				start_tile = self._getPosition(tile, 0-index, direction)
				# exceeds board size, continue
				if not start_tile:
					continue
				# try and build the word around the pivot
				for letter_pos in range(0, len(word)):
					# don't need to check pivot
					if letter_pos-index != 0:
						tile_pos = self._getPosition(tile, letter_pos-index, direction)
						if tile_pos in self.tiles_in_play:
							if self.tiles_in_play[tile_pos]['letter'] != word[letter_pos]:
								# CHARACTER MISMATCH - ALREADY ON THE BOARD, BREAK
								validWord = False
								break
						else:
							side_word = ''
							# check up if 'across', left if 'down'
							up_tile_pos = self._getPosition(tile_pos, -1, other_direction)
							if up_tile_pos in self.tiles_in_play:
								if self.tiles_in_play[up_tile_pos][other_direction]:
									side_word = self.tiles_in_play[up_tile_pos][other_direction]
								else:
									side_word = self.tiles_in_play[up_tile_pos]['letter']

							# add pivot letter
							side_word = side_word + pivot

							# check down if 'across', right if 'down'
							down_tile_pos = self._getPosition(tile_pos, 1, other_direction)
							if down_tile_pos in self.tiles_in_play:
								if self.tiles_in_play[down_tile_pos][other_direction]:
									side_word += self.tiles_in_play[down_tile_pos][other_direction]
								else:
									side_word += self.tiles_in_play[down_tile_pos]['letter']

							# check if side_word is a valid word
							if side_word != pivot and not self._checkWord(side_word):
								# SIDE WORD IS NOT A VALID WORD, BREAK
								validWord = False
								break
				# word is valid, add (word, tile, direction) tuple to return list
				if validWord:
					valid_words.append((word, start_tile, direction))
				start_pos = index + 1
		return valid_words


	# find best possible word player can create on a tile
	def _findMostPoints(self, letters_in_hand, tile):
		possible_words = self._findPossibleWords(list(letters_in_hand), self.tiles_in_play[tile]['letter'])
		print 'pivot: '+str(self.tiles_in_play[tile]['letter']) + '  ' + str( possible_words )
		valid_words = self._checkWordPlacement(possible_words, tile)
		print '   valid_words: ' + str(valid_words)
		return (None, None, None, None)


	# get next optimal move
	def findOptimal(self, player):
		bestMove = False
		for tile in self.tiles_in_play:
			if not (self.tiles_in_play[tile]['across'] and self.tiles_in_play[tile]['down']):
				#sys.stderr.write("i am tile: " + str(tile) + ' and my letter is: ' + str(self.tiles_in_play[tile]['letter'])+'\n')
				(word, tile, direction, points) = self._findMostPoints(self.letters_in_hand[player], tile)

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
