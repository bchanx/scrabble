#!/usr/bin/env python

import os
import sys
import shutil
import random
import ConfigParser

# global variables
DEBUG = False
DOWN = 'down'
ACROSS = 'across'
CONFIG_DIR = '../config'
CONFIG_FILE = os.path.join(CONFIG_DIR, 'scrabble.conf')
DICTIONARY_FILE = os.path.join(CONFIG_DIR, 'basic_english_word_list')
LETTER_MAP = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'blank']

class Scrabble:

	def __init__(self, player_size, config_file, dictionary_file):
		# initialize word list
		allwords = open(dictionary_file).read().split()
		self.dictionary = set(w for w in allwords if len(w) >= 2)

		# initialize board rules
		config = ConfigParser.ConfigParser()
		config.read(config_file)
		self.board_size = config.getint('init', 'board_size')
		self.rack_size = config.getint('init', 'rack_size')
		self.center_tile = config.get('init', 'center_tile')
		self.double_letter = config.get('init', 'double_letter').split('/')
		self.triple_letter = config.get('init', 'triple_letter').split('/')
		self.double_word = config.get('init', 'double_word').split('/')
		self.triple_word = config.get('init', 'triple_word').split('/')

		# initialize letters
		self.letters = {}
		self.letters_points = {}
		self.letters_remaining = 0
		for l in LETTER_MAP:
			count, points = config.get('letters', l).split('/')
			self.letters[l] = int(count)
			self.letters_points[l] = int(points)
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
				letter_placements = self._parseWord(word, tile, direction)
				self._addWordInPlay(letter_placements, word.replace('?', '') , tile, direction)
				self._reduceLetters(letter_placements.values())

		# initialize players
		self.player_size = player_size
		self.player_list = []
		self.player_index = 0
		for num in range(0, player_size):
			self.player_list.append('player'+str(num))
		self.player = self.player_list[self.player_index]

		# initialize player data
		self.player_data = {}
		for player in self.player_list:
			self.player_data[player] = {}
			self.player_data[player]['score'] = 0
			init_letters = config.get('letters_in_hand', player)
			if init_letters:
				self.player_data[player]['letters_in_hand'] = init_letters.split('/')
				self._reduceLetters(self.player_data[player]['letters_in_hand'])
			else:
				self.player_data[player]['letters_in_hand'] = []
				self._getTiles(player)


	# parse word from config file to get letter_placements
	def _parseWord(self, word, tile, direction):
		letter_placements = {}
		letter_pos = 0
		while letter_pos < len(word):
			current_placement = word[letter_pos]
			if word[letter_pos] == '?':
				letter_pos += 1
				current_placement = 'blank'
			if tile not in self.tiles_in_play:
				letter_placements[tile] = current_placement
			elif self.tiles_in_play[tile]['letter'] != word[letter_pos]:
				exit('FATAL ERROR: letter in word does not match! (tile: '+str(tile)+'  placed: '+str(self.tiles_in_play[tile]['letter'])+ '  trying to add: '+str(word[letter_pos])+')')
			tile = self._getPosition(tile, 1, direction)
			letter_pos += 1
		return letter_placements


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


	# reduce letters from letters_remaining and letter map
	def _reduceLetters(self, letters):
		for l in letters:
			if l not in self.letters:
				exit('FATAL ERROR: not enough letters to continue. (letter: '+str(l)+')')
			self.letters_remaining -= 1
			self.letters[l] -= 1
			if self.letters[l] == 0:
				del self.letters[l]


	# get new tiles for rack (until letters_remaining = 0 or letters_in_hand = rack_size)
	def _getTiles(self, player):
		while (len(self.player_data[player]['letters_in_hand']) < self.rack_size) and (self.letters_remaining > 0):
			l = random.choice(self.letters.keys())
			self.player_data[player]['letters_in_hand'].append(l)
			self._reduceLetters([l])


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
	def _addWordInPlay(self, letter_placements, word, tile, direction):
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
				self.tiles_in_play[tile_pos]['points'] = self.letters_points[letter_placements[tile_pos]]
				self.tiles_in_play[tile_pos][direction] = {}
				self.tiles_in_play[tile_pos][direction]['word'] = word
				self.tiles_in_play[tile_pos][direction]['start'] = tile
				
				# check whether previous or next tiles need to be updated
				other_direction = self._getOtherDirection(direction)
				self.tiles_in_play[tile_pos][other_direction] = {}
				sideWord = self._checkSideWord(tile_pos, letter, other_direction)

				# side word created, assume its valid at this point
				if sideWord:
					side_word = sideWord['word']
					side_start_tile = sideWord['start']
					# check prev and next positions
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
						self.words_in_play[side_word]['placements'] = []
						self.words_in_play[side_word]['shortest'] = self._getShortestLetter(word)
					self.words_in_play[side_word]['placements'].append(side_start_tile+';'+other_direction)
			# update tile position
			tile_pos = self._getPosition(tile_pos, 1, direction)
		if word not in self.words_in_play:
			self.words_in_play[word] = {}
			self.words_in_play[word]['placements'] = []
			self.words_in_play[word]['shortest'] = self._getShortestLetter(word)
		self.words_in_play[word]['placements'].append(tile+';'+direction)


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
				placement_key = old_start_pos+';'+other_direction
				if placement_key in self.words_in_play[old_word]['placements']:
					self.words_in_play[old_word]['placements'].remove(placement_key)
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


	# get next optimal move
	def getOptimalMove(self):
		optimalMap = {}
		optimalMap['points'] = 0
		optimalMap['words'] = []
		letters_in_hand = self.player_data[self.player]['letters_in_hand']

		# no tiles or words in play
		if not self.tiles_in_play:
			if DEBUG: print '== checking no tiles or words in play =='
			valid_placements = self._getCreatableWords(self.center_tile, letters_in_hand)
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
			valid_placements = []
			for word_played in self.words_in_play:
				word_dict = self.possible_words[self.words_in_play[word_played]['shortest']]
				word_list = []
				for word in word_dict:
					if word_played != word and word_played in word:
						word_list.append(word)
				# go through sub list of possible words
				for word in word_list:
					for placement_key in self.words_in_play[word_played]['placements']:
						tile, direction = placement_key.split(';')
						valid_word_placements = self._checkPlacement(word_played, word, tile, direction, letters_in_hand)
						if valid_word_placements:
							for w, t, d, l in valid_word_placements:
								# if letters used == 1, check for additional possible words to make on new pivot
								if len(l) == 1:
									pivot_index = word.find(word_played)
									if (pivot_index == 0):
										sub_pivot = word[len(word_played)]
										sub_tile = self._getPosition(t, len(word_played), direction)
									else:
										sub_pivot = word[pivot_index-1]
										sub_tile = self._getPosition(t, pivot_index-1, direction)
									sub_direction = self._getOtherDirection(direction)
									sub_dict = self.possible_words[sub_pivot]
									for sub_word in sub_dict:
										sub_placements = self._checkPlacement(sub_pivot, sub_word, sub_tile, sub_direction, letters_in_hand)
										if sub_placements:
											for sw, st, sd, sl in sub_placements:
												sl.sort()
												if (sw, st, sd, sl) not in valid_placements:
													valid_placements.append((sw, st, sd, sl))
								l.sort()
								if (w, t, d, l) not in valid_placements:
									valid_placements.append((w, t, d, l))
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
				# optimize letter placement
				letter_placements = self._optimizeLetters(letters_in_hand, w, t, d, l)
				if letter_placements:
					points = self._checkWordScore(letter_placements, w, t, d)
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
			# case when board is empty
			if tile_pos == self.center_tile: validPosition = True

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


	# optimize placement of letters
	def _optimizeLetters(self, letters_in_hand, word, tile, direction, letters_used):
		letter_placements = {}
		tmpletters = list(letters_in_hand)
		other_direction = self._getOtherDirection(direction)
		for i in range(0, len(word)):
			letter = word[i]
			# letter already exists on board
			if tile in self.tiles_in_play:
				# ERROR: letter in word doesn't match letter on board (should have failed placement check)
				if self.tiles_in_play[tile]['letter'] != letter:
					return False
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
				return False
			# update tile pos
			tmpletters.remove(letter_used)
			letter_placements[tile] = letter_used
			tile = self._getPosition(tile, 1, direction)
		return letter_placements


	# find the score of a word placement
	def _checkWordScore(self, letter_placements, word, tile, direction):
		other_direction = self._getOtherDirection(direction)
		main_multiplier = 1
		main_points = side_points = bonus_points = 0
		for i in range(0, len(word)):
			# letter already exists on board, grab letter face value
			if tile in self.tiles_in_play:
				# ERROR: letter in word doesn't match letter on board (should have failed placement check)
				if self.tiles_in_play[tile]['letter'] != word[i]:
					return 0
				main_points += self.tiles_in_play[tile]['points']
				tile = self._getPosition(tile, 1, direction)
				continue
			# grab letter from letter_placements
			elif tile in letter_placements:
				letter_used = letter_placements[tile]
			# ERROR: impossible to create word (should have failed placement check)
			else:
				return 0
			# get current letter points and remove letter used from hand
			current_letter_points = self.letters_points[letter_used] * self._getLetterMultiplier(tile)
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
		if len(letter_placements) == 7:
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
	def getLetters(self):
		return self.player_data[self.player]['letters_in_hand']


	# return current player score
	def getScore(self):
		return self.player_data[self.player]['score']


	# return current player
	def getPlayer(self):
		return self.player


	# return prettified scrabble board
	def getBoard(self):
		bold = '\033[1m'
		reset = '\033[0;0m'
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
					elif tile in self.tiles_in_play:
						output += bold
						output += self.tiles_in_play[tile]['letter'].upper()
						if self.tiles_in_play[tile]['points'] == 0:
							output = output+'?'+reset
						else: output = output+reset+' '
						output += '  |'
					elif tile in self.double_letter: output += '*   |'
					elif tile in self.triple_letter: output += '#   |'
					elif tile in self.double_word: output += 'x2  |'
					elif tile in self.triple_word: output += 'x3  |'
					else: output += '    |'
				output += '\n'
		return output


	# place a word onto the board. return word score if successful, false otherwise.
	def placeWord(self, word, tile, direction):
		# check if word is valid word
		if not self._checkWord(word):
			return False
		# check placement (check whether word can be placed, and if user has enough letters)
		letters_in_hand = self.player_data[self.player]['letters_in_hand']
		valid_placements = self._validatePlacement(word, tile, direction, letters_in_hand)
		if not valid_placements:
			return False
		# get letter placement (TODO: should not auto optimize for users, will provide letter_placement if UI is made)
		w, t, d, letters_used = valid_placements[0]
		letter_placements = self._optimizeLetters(letters_in_hand, w, t, d, letters_used)
		if not letter_placements:
			return False
		# get score
		word_score = self._checkWordScore(letter_placements, w, t, d)
		self.player_data[self.player]['score'] += word_score
		# place word
		self._addWordInPlay(letter_placements, w, t, d)
		# discard letters used
		for l in letters_used: self.player_data[self.player]['letters_in_hand'].remove(l)
		# get new tiles
		self._getTiles(self.player)
		# switch to next player
		self.nextPlayer()
		return word_score


	# exchange letters in hand for new tiles. returns True if successful, false otherwise.
	def exchangeTiles(self, exchange_tiles):
		# make sure player has the exchange tiles
		for l in exchange_tiles:
			if exchange_tiles.count(l) > self.player_data[self.player]['letters_in_hand'].count(l):
				return False
		# make sure enough tiles remaining to do exchange
		if len(exchange_tiles) > self.letters_remaining: return False
		# remove tiles from player
		for l in exchange_tiles: self.player_data[self.player]['letters_in_hand'].remove(l)
		# get new tiles
		self._getTiles(self.player)
		# put back exchange_tiles
		self._insertTiles(exchange_tiles)
		# switch to next player
		self.nextPlayer()
		return True


	# insert tiles back into play
	def _insertTiles(self, exchange_tiles):
		for l in exchange_tiles:
			if l not in self.letters: self.letters[l] = 1
			else: self.letters[l] += 1
		self.letters_remaining += len(exchange_tiles)


	# switch to next player
	def nextPlayer(self):
		self.player_index = (self.player_index+1)%self.player_size
		self.player = self.player_list[self.player_index]


# (TODO) polish user input shell capability
if __name__ == '__main__':
	# initialize the game
	scrabble = Scrabble(1, CONFIG_FILE, DICTIONARY_FILE)
	while (True):
		# print current state of the game
		print scrabble.getBoard()
		print str(scrabble.getPlayer())+' - '+str(scrabble.getScore())+' points - '+ str(scrabble.getLetters())
		print 'Available commands:  [help] [exit] [place] [optimal] [pass] [exchange]'

		while(True):
			# get user input
			stdin = raw_input('>> ')
			stdin = stdin.split(' ')
			cmd = stdin[0]

			# show help
			if (cmd == 'help'):
				print 'no help available, better luck next time.'
				continue
			# exit
			elif (cmd == 'exit'):
				exit()
			# place word onto board
			elif (cmd == 'place'):
				if len(stdin) != 4:
					print 'invalid input: place [WORD] [TILE] [DIRECTION]'
					continue
				word = stdin[1]
				tile = stdin[2]
				direction = stdin[3]
				score = scrabble.placeWord(word, tile, direction)
				if not score:
					print 'invalid input: word could not be placed!'
					continue
				print 'SCORE for '+str(word)+': '+str(score)+' points!'
				break
			# get optimal move
			elif (cmd == 'optimal'):
				optimal = scrabble.getOptimalMove()
				if not optimal:
					print 'no possible words can be created!'
					continue
				print 'optimal: '+str(optimal)
			# pass your turn
			elif (cmd == 'pass'):
				scrabble.nextPlayer()
				break
			# exchange tiles
			elif (cmd == 'exchange'):
				exchange_tiles = []
				for letter in range(1, len(stdin)):
					exchange_tiles.append(stdin[letter])
				if not scrabble.exchangeTiles(exchange_tiles):
					print 'invalid exchange!'
					continue
				break
			# unknown
			else:
				print 'unknown command!'

