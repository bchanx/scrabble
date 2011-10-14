#!/usr/bin/env python

import os
import sys
import shutil
import random
import ConfigParser

# global variables
DEBUG = True
DOWN = 'down'
ACROSS = 'across'
CONFIG_DIR = './config'
CONFIG_FILE = os.path.join(CONFIG_DIR, 'scrabble.conf')
DICTIONARY_FILE = os.path.join(CONFIG_DIR, 'basic_english_word_list')
LETTER_MAP = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'blank']

class Scrabble:

	def __init__(self):
		# initialize word list
		allwords = open(DICTIONARY_FILE).read().split()
		self.dictionary = set(w for w in allwords if len(w) >= 2)

		# initialize board rules
		config = ConfigParser.ConfigParser()
		config.read(CONFIG_FILE)
		self.board_size = config.getint('init', 'board_size')
		self.rack_size = config.getint('init', 'rack_size')
		self.player_size = config.getint('init', 'player_size')
		self.double_letter = config.get('init', 'double_letter').split('/')
		self.triple_letter = config.get('init', 'triple_letter').split('/')
		self.double_word = config.get('init', 'double_word').split('/')
		self.triple_word = config.get('init', 'triple_word').split('/')

		# initialize letters
		self.letters = {}
		self.letters_remaining = 0
		for l in LETTER_MAP:
			count, points = config.get('letters', l).split('/')
			self.letters[l] = {}
			self.letters[l]['count'] = int(count)
			self.letters[l]['points'] = int(points)
			self.letters_remaining += int(count)

		# initialize possible words per letter
		self.possible_words = {}
		for l in LETTER_MAP:
			if l != 'blank':
				self.possible_words[l] = []
		for word in self.dictionary:
			for l in LETTER_MAP:
				if l != 'blank' and l in word and word not in self.possible_words[l]:
					self.possible_words[l].append(word)

		# initialize current words in play
		self.words_in_play = {}
		self.tiles_in_play = {}
		words_in_play = config.get('init', 'words_in_play')
		if words_in_play:
			words_and_position = words_in_play.split('/')
			for words in words_and_position:
				word, tile, direction = words.split(';')
				self._addWordInPlay(word, tile, direction)
				print self.words_in_play

		# initialize player data
		self.player_data = {}
		for num in range(0, self.player_size):
			player = 'player'+str(num)
			self.player_data[player] = {}
			self.player_data[player]['score'] = 0

			init_letters = config.get('letters_in_hand', player)
			if init_letters:
				self.player_data[player]['letters_in_hand'] = init_letters.split('/')
			else:
				self.player_data[player]['letters_in_hand'] = []
				random.seed()
				while (len(self.player_data[player]['letters_in_hand']) < self.rack_size) and (self.letters_remaining > 0):
					l = LETTER_MAP[random.randint(0, len(LETTER_MAP)-1)]
					if self.letters[l]['count'] > 0:
						self.player_data[player]['letters_in_hand'].append(l)
						self.letters[l]['count'] -= 1
						self.letters_remaining -= 1


	# get letter with the shortest dictionary
	def _getShortestLetter(self, word):
		shortest_length = sys.maxint
		shortest_letter = ''
		for letter in set(word):
			if len(self.possible_words[letter]) < shortest_length:
				shortest_length = len(self.possible_words[letter])
				shortest_letter = letter
		return shortest_letter


	# update words_in_play and tiles_in_play with word
	def _addWordInPlay(self, word, tile, direction):
		tile_pos = tile
		for letter in word:
			# already in map, update direction
			if tile_pos in self.tiles_in_play:
				if not self.tiles_in_play[tile_pos][direction]:
					self.tiles_in_play[tile_pos][direction]  = {}
				self.tiles_in_play[tile_pos][direction]['word'] = word
				self.tiles_in_play[tile_pos][direction]['start'] = tile
			else:
				# letter not in map, create it
				self.tiles_in_play[tile_pos] = {}
				self.tiles_in_play[tile_pos]['letter'] = letter
				self.tiles_in_play[tile_pos]['points'] = self.letters[letter]['points']
				self.tiles_in_play[tile_pos][direction] = {}
				self.tiles_in_play[tile_pos][direction]['word'] = word
				self.tiles_in_play[tile_pos][direction]['start'] = tile
				
				# check whether previous or next tiles need to be updated
				other_direction = self._getOtherDirection(direction)
				sideWord = self._checkSideWord(tile_pos, letter, other_direction)
				self.tiles_in_play[tile_pos][other_direction] = {}

				# side word created, assume its valid at this point
				if sideWord:
					side_word = sideWord['word']
					side_start_tile = sideWord['start']

					prev_pos = self._getPosition(tile_pos, -1, other_direction)
					next_pos = self._getPosition(tile_pos, 1, other_direction)
					if prev_pos in self.tiles_in_play:
						self._updateTiles(side_word, side_start_tile, prev_pos, other_direction)
					if next_pos in self.tiles_in_play:
						self._updateTiles(side_word, side_start_tile, next_pos, other_direction)
					self.tiles_in_play[tile_pos][other_direction]['word'] = side_word
					self.tiles_in_play[tile_pos][other_direction]['start'] = side_start_tile
					# add sideword to words_in_play
					if side_word not in self.words_in_play:
						self.words_in_play[side_word] = {}
						self.words_in_play[side_word]['placements'] = {}
						self.words_in_play[side_word]['shortest'] = self._getShortestLetter(word)
					self.words_in_play[side_word]['placements'][side_start_tile] = direction
				else:
					self.tiles_in_play[tile_pos][other_direction] = None
			# update tile position
			tile_pos = self._getPosition(tile_pos, 1, direction)
		if word not in self.words_in_play:
			self.words_in_play[word] = {}
			self.words_in_play[word]['placements'] = {}
			self.words_in_play[word]['shortest'] = self._getShortestLetter(word)
		self.words_in_play[word]['placements'][tile] = direction


	# update tiles_in_play and words_in_play with new data
	def _updateTiles(self, new_word, new_start_tile, tile, other_direction):
		# do cleanup if tile is currently a word
		if self.tiles_in_play[tile][other_direction]:
			old_start_pos = self.tiles_in_play[tile][other_direction]['start']
			old_word = self.tiles_in_play[tile][other_direction]['word']
			old_word_length = len(old_word)
			tile_pos = old_start_pos
			for i in range(0, old_word_length):
				self.tiles_in_play[tile_pos][other_direction]['word'] = new_word
				self.tiles_in_play[tile_pos][other_direction]['start'] = new_start_tile
				tile_pos = self._getPosition(tile_pos, 1, other_direction)
			# do cleanup in self.words_in_play
			if old_word in self.words_in_play:
				if old_start_pos in self.words_in_play[old_word]['placements']:
					del self.words_in_play[old_word]['placements'][old_start_pos]
					if not self.words_in_play[old_word]['placements']:
						del self.words_in_play[old_word]
		# else tile is only a letter
		else:
			self.tiles_in_play[tile][other_direction]['word'] = new_word
			self.tiles_in_play[tile][other_direction]['start'] = new_start_tile
		


	# check surrounding tiles to see whether side word can be created
	def _checkSideWord(self, tile, current_letter, other_direction):
		sideWord = {}
		side_word_start = tile

		# checking surrounding letters; check up if ACROSS, left if DOWN
		prev_word = ''
		prev_tile = self._getPosition(tile, -1, other_direction)
		if prev_tile in self.tiles_in_play:
			if self.tiles_in_play[prev_tile][other_direction]:
				prev_word = self.tiles_in_play[prev_tile][other_direction]['word']
				side_word_start = self.tiles_in_play[prev_tile][other_direction]['start']
			else:
				prev_word = self.tiles_in_play[prev_tile]['letter']
				side_word_start = prev_tile
		# checking surrounding letters; check down if ACROSS, right if DOWN
		next_word = ''
		next_tile = self._getPosition(tile, 1, other_direction)
		if next_tile in self.tiles_in_play:
			if self.tiles_in_play[next_tile][other_direction]:
				next_word += self.tiles_in_play[next_tile][other_direction]['word']
			else:
				next_word += self.tiles_in_play[next_tile]['letter']
		# if surrounding letters exist, return resulting word created
		if prev_word or next_word:
			sideWord['word'] = prev_word + current_letter + next_word
			sideWord['start'] = side_word_start
		return sideWord


	# get other direction
	def _getOtherDirection(self, direction):
		if direction == ACROSS: return DOWN
		return ACROSS


	# Returns new position if successful, False if outside board size.
	def _getPosition(self, tile, length, direction):
		if direction == ACROSS:
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


	# get next optimal move
	def getOptimalMove(self, player):
		optimalMap = {}
		optimalMap['points'] = 0
		optimalMap['words'] = []
		letters_in_hand = self.player_data[player]['letters_in_hand']

		# no tiles or words in play
		if not self.tiles_in_play:
			if DEBUG: print '== checking no tiles or words in play =='
			valid_placements = self._getCreatableWords('7-7', letters_in_hand)
			if valid_placements:
				# get optimal words and points
				self._getOptimalPlacement(optimalMap, valid_placements, letters_in_hand)
		else:
			# check current tiles in play
			if DEBUG: print '== checking current tiles in play =='
			for tile in self.tiles_in_play:
				if not (self.tiles_in_play[tile][ACROSS] and self.tiles_in_play[tile][DOWN]):
					pivot = self.tiles_in_play[tile]['letter']
					possible_words = self.possible_words[pivot]
					for word in possible_words:
						if not self.tiles_in_play[tile][ACROSS]: direction = ACROSS
						else: direction = DOWN
						valid_placements = self._checkPlacement(pivot, word, tile, direction, letters_in_hand)
						if valid_placements:
							# get optimal words and points
							self._getOptimalPlacement(optimalMap, valid_placements, letters_in_hand)
			
			# check current words in play
			if DEBUG: print '== checking current words in play =='
			for word_played in self.words_in_play:
				word_dict = self.possible_words[self.words_in_play[word_played]['shortest']]
				word_list = []
				for word in word_dict:
					if word_played != word and word_played in word:
						word_list.append(word)
				# go through sub list of possible words
				for word in word_list:
					for placement in self.words_in_play[word_played]['placements']:
						tile = placement
						direction = self.words_in_play[word_played]['placements'][tile]
						valid_placements = self._checkPlacement(word_played, word, tile, direction, letters_in_hand)

						valid_sub_placements = []
						if valid_placements:
							for w, t, d, l in valid_placements:
								# if letters used == 1, check for additional possible words to make on new pivot
								if len(l) == 1:
									sub_pivot = l[0]
									if t in self.tiles_in_play: sub_tile = self._getPosition(t, len(w)-1, direction)
									else: sub_tile = t
									sub_direction = self._getOtherDirection(direction)
									sub_dict = self.possible_words[sub_pivot]
									for sub_word in sub_dict:
										sub_placements = self._checkPlacement(sub_pivot, sub_word, sub_tile, sub_direction, letters_in_hand)
										if sub_placements:
											for sw, st, sd, sl in sub_placements:
												valid_sub_placements.append((sw, st, sd, sl))

							# add valid sub placements to placement list
							valid_placements.extend(valid_sub_placements)
							# get optimal words and points
							self._getOptimalPlacement(optimalMap, valid_placements, letters_in_hand)
		return optimalMap


	# get all creatable words from letters in hand
	def _getCreatableWords(self, start_tile, letters_in_hand):
		creatable_words = []
		for word in self.dictionary:
			letters_used = self._letterCheck(word, letters_in_hand)
			if letters_used:
				if len(word) > 4:
					for i in range (0, len(word)):
						creatable_words.append((word, self._getPosition(start_tile, -i, ACROSS), ACROSS, letters_used))
				else:
					creatable_words.append((word, start_tile, ACROSS, letters_used))
		return creatable_words


	# returns letters_used if letters_needed is a subset of letters_in_hand, False otherwise.
	def _letterCheck(self, letters_needed, letters_in_hand):
		letters_used = []
		if len(letters_in_hand) < len(letters_needed):
			return False
		tmpletters = list(letters_in_hand)
		for l in letters_needed:
			if not letters_needed.count(l) <= tmpletters.count(l):
				# check blanks
				if 'blank' in tmpletters:
					if (letters_needed.count(l) - tmpletters.count(l)) <= tmpletters.count('blank'):
						tmpletters.remove('blank')
						tmpletters.append(l)
						letters_used.append('blank')
						continue
				# not possible
				return False
			letters_used.append(l)
		return letters_used


	# find optimal placement from list of valid placements
	def _getOptimalPlacement(self, optimalMap, valid_placements, letters_in_hand):
		for w, t, d, l in valid_placements:
			l.sort()
			if (w, t, d, l) not in optimalMap['words']:
				points = self._checkWordScore(letters_in_hand, w, t, d)
				if DEBUG: print '\tPOINTS: '+str(points)+'\tWORD: '+str(w)+'\tTILE: '+str(t)+'\tDIR: '+str(d)+'\tLETTERS_USED: '+str(l)
				if points > optimalMap['points']:
					del optimalMap['words'][:]
					optimalMap['words'].append((w, t, d, l))
					optimalMap['points'] = points
				elif points == optimalMap['points']:
					optimalMap['words'].append((w, t, d, l))


	# check all possible placements of a word around pivot
	def _checkPlacement(self, pivot, word, tile, direction, letters_in_hand):
		valid_placements = []
		start_pos = 0
		end_pos = len(word)

		# find position of each pivot in the word
		for i in range(0, word.count(pivot)):
			letters_needed = []
			pivot_pos = word.find(pivot, start_pos, end_pos)
			start_tile = self._getPosition(tile, 0-pivot_pos, direction)
			# check if placement is valid
			validPlacement = self._validatePlacement(word, start_tile, direction, letters_in_hand)
			if validPlacement: valid_placements.extend(validPlacement)
			start_pos = pivot_pos + 1
		return valid_placements


	# check whether a word can be placed in direction from start_tile, if enough letters to create, and if extends miminum 1 current letter on board
	def _validatePlacement(self, word, start_tile, direction, letters_in_hand):
		# start of word exceeds board size, discard rest of checking
		if not start_tile: return False

		valid_placements = []
		letters_needed = []
		other_direction = self._getOtherDirection(direction)
		validPlacement = True
		validPosition = False
		letter_pos = 0
		# try and build the word, check letters
		while letter_pos < len(word):
			tile_pos = self._getPosition(start_tile, letter_pos, direction)
			if not tile_pos:
				# word too long; exceeds board size, break
				validPlacement = False
				break
			elif tile_pos in self.tiles_in_play:
				validPosition = True
				# a different letter already on the board, break
				if self.tiles_in_play[tile_pos]['letter'] != word[letter_pos]:
					validPlacement = False
					break
				# letter is already on the board, continue
				else:
					letter_pos += 1
					continue
			else:
				# check surrounding letters to see if side word is created
				side_word = self._checkSideWord(tile_pos, word[letter_pos], other_direction)
				if side_word:
					validPosition = True
					# side word is not valid, break
					if not self._checkWord(side_word['word']):
						validPlacement = False
						break
				# add current letter to letter check
				letters_needed.append(word[letter_pos])
			letter_pos += 1
		# tile placement is valid
		if validPlacement and validPosition:
			# check if player has enough letters and if boundaries are clean
			letters_used = self._letterCheck(letters_needed, letters_in_hand)
			if letters_used and self._boundaryCheck(len(word), start_tile, direction):
				# word is good, add (word, tile, direction, letters_used) tuple to return
				valid_placements.append((word, start_tile, direction, letters_used))
		return valid_placements


	# check whether word exists in dictionary
	def _checkWord(self, word):
		return word in self.dictionary


	# check whether letter exists before and after word
	def _boundaryCheck(self, word_length, tile, direction):
		prev_pos = self._getPosition(tile, -1, direction)
		if prev_pos and prev_pos in self.tiles_in_play: return False
		next_pos = self._getPosition(tile, word_length, direction)
		if next_pos and next_pos in self.tiles_in_play: return False
		return True


	# find the score of a word placement
	# (TODO) Add tile placement metadata for letters_used
	def _checkWordScore(self, letters_in_hand, word, tile, direction):
		tmpletters = list(letters_in_hand)
		other_direction = self._getOtherDirection(direction)
		main_multiplier = 1
		main_points = side_points = bonus_points = 0
		for i in range(0, len(word)):
			letter = word[i]

			# letter already exists on board, grab letter face value
			if tile in self.tiles_in_play:
				# ERROR: letter in word doesn't match letter on board (should have failed placement check)
				if self.tiles_in_play[tile]['letter'] != letter:
					return 0
				main_points += self.tiles_in_play[tile]['points']
				tile = self._getPosition(tile, 1, direction)
				continue

			# choose which letter from hand to use for optimal points
			if letter in tmpletters:
				letter_used = letter
				if 'blank' in tmpletters:
					remaining_word = word[i:]
					if remaining_word.count(letter) > tmpletters.count(letter):
						if self._useBlankTile(remaining_word, letter, tile, direction):
							letter_used = 'blank'
			# use a blank letter tile
			elif 'blank' in tmpletters:
				letter_used = 'blank'
			# ERROR: impossible to create word (should have failed placement check)
			else:
				return 0

			# get current letter points and remove letter used from hand
			current_letter_points = self.letters[letter_used]['points'] * self._getLetterMultiplier(tile)
			tmpletters.remove(letter_used)

			# update word multiplier
			current_multiplier = self._getWordMultiplier(tile)
			main_multiplier *= current_multiplier

			# get side points
			current_side_points = 0
			prev_tile_pos = self._getPosition(tile, -1, other_direction)
			next_tile_pos = self._getPosition(tile, 1, other_direction)
			if prev_tile_pos in self.tiles_in_play or next_tile_pos in self.tiles_in_play:
				current_side_points += self._getTileScore(prev_tile_pos, -1, other_direction)
				current_side_points += self._getTileScore(next_tile_pos, 1, other_direction)
				current_side_points += current_letter_points
				side_points += current_side_points * current_multiplier

			# update main_points
			main_points += current_letter_points

			# update tile pos
			tile = self._getPosition(tile, 1, direction)

		# apply main multiplier to main points
		main_points *= main_multiplier
		# 7 letters used, 50 point bonus!
		if len(letters_in_hand) == 7 and len(tmpletters) == 0:
			bonus_points = 50
		return main_points + side_points + bonus_points


	# choose whether to use regular or blank tile
	def _useBlankTile(self, remaining_word, letter, tile, direction):
		other_direction = self._getOtherDirection(direction)
		current_bonus = self._getTileBonus(tile, other_direction)
		for l in remaining_word[1:]:
			tile = self._getPosition(tile, 1, direction)
			if l == letter and tile not in self.tiles_in_play:
				future_bonus = self._getTileBonus(tile, other_direction)
				if future_bonus > current_bonus:
					return True
		return False


	# get tile bonus based on tile multiplier and how many words it is in
	def _getTileBonus(self, tile, other_direction):
		if self._tileInTwoWords(tile, other_direction):
			if self._tileIsLetterMultiplier(tile):
				return self._getLetterMultiplier(tile) * 2
			elif self._tileIsWordMultiplier(tile): 
				return self._getWordMultiplier(tile)
		else:
			if self._tileIsLetterMultiplier(tile): 
				return self._getLetterMultiplier(tile)
		return 1


	# check whether a tile is part of two words (across and down)
	def _tileInTwoWords(self, tile, other_direction):
		before = self._getPosition(tile, -1, other_direction)
		after = self._getPosition(tile, 1, other_direction)
		if before in self.tiles_in_play or after in self.tiles_in_play:
			return True
		return False


	# check whether tile is a letter multiplier
	def _tileIsLetterMultiplier(self, tile):
		if tile in self.triple_letter or tile in self.double_letter: return True
		return False


	# check whether tile is a word multiplier
	def _tileIsWordMultiplier(self, tile):
		if tile in self.triple_word or tile in self.double_word: return True
		return False


	# return letter multiplier
	def _getLetterMultiplier(self, tile):
		if tile in self.triple_letter: return 3
		elif tile in self.double_letter: return 2
		return 1


	# return word multiplier
	def _getWordMultiplier(self, tile):
		if tile in self.triple_word: return 3
		elif tile in self.double_word: return 2
		return 1


	# return accumulative score from adjacent tiles in a direction
	def _getTileScore(self, tile, length, direction):
		tile_score = 0
		while tile in self.tiles_in_play:
			tile_score += self.tiles_in_play[tile]['points']
			tile = self._getPosition(tile, length, direction)
		return tile_score


	# return current letters in hand
	def getLetters(self, player):
		return self.player_data[player]['letters_in_hand']


	# return prettified scrabble board
	def getBoard(self):
		output = '     '
		for col in range(0, self.board_size):
			output += str(col)
			if len(str(col)) == 1: output += '    '
			else: output += '   '
		output += '\n\n'

		for row in range(0, self.board_size):
			for i in range (0, 2):
				if i == 0:
					output += str(row)
					if len(str(row)) == 1: output += '   |'
					else: output += '  |'
				else: output += '    |'
				for col in range(0, self.board_size):
					tile = str(row) + '-' + str(col)
					if i == 1: output += '____|'
					elif tile in self.tiles_in_play: output += self.tiles_in_play[tile]['letter'].upper() + '   |'
					elif tile in self.double_letter: output += '*   |'
					elif tile in self.triple_letter: output += '#   |'
					elif tile in self.double_word: output += 'x2  |'
					elif tile in self.triple_word: output += 'x3  |'
					else: output += '    |'
				output += '\n'
		return output


	# place a word onto the board
	def placeWord(self, player, word, tile, direction):
		letters_in_hand = self.player_data[player]['letters_in_hand']

		# check placement (check whether word can be placed, and if user has enough letters)
		valid_placements = self._validatePlacement(word, tile, direction, letters_in_hand)
		if valid_placements:
			# get score
			self.player_data[player]['score'] += self._checkWordScore(letters_in_hand, word, tile, direction)

			# place word
			self._addWordInPlay(word, tile, direction)
			
			# (TODO) get new tiles
		print str(self.getBoard())
		return


	# exchange letters in hand for new tiles
	def exchangeTiles(self, player, exchange_tiles):
		# make sure remaining tiles >= len(exchange_tiles)
		# get new tiles
		# put back exchange_tiles
		return


# (TODO) add user input shell capability
if __name__ == '__main__':
	scrabble = Scrabble()
	print scrabble.getBoard()
	print 'letters in hand: '+ str(scrabble.getLetters('player0'))
	print 'optimal move: '+str(scrabble.getOptimalMove('player0'))
	#scrabble.placeWord('player0', 'rain', '5-9', DOWN)
