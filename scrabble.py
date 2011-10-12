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
				self.words_in_play[word] = {}
				self.words_in_play[word]['start'] = tile
				self.words_in_play[word]['direction'] = direction
				self.words_in_play[word]['shortest'] = self._getShortestLetter(word)
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
					l = LETTER_MAP[random.randint(0, len(LETTER_MAP)-1)]
					if self.letters[l]['count'] > 0:
						self.letters_in_hand[player].append(l)
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
				if direction == ACROSS:
					self.tiles_in_play[cur_tile][ACROSS] = word
					self.tiles_in_play[cur_tile][DOWN] = None
				else:
					self.tiles_in_play[cur_tile][ACROSS] = None
					self.tiles_in_play[cur_tile][DOWN] = word
				self.tiles_in_play[cur_tile]['points'] = self.letters[letter]['points']
				self.tiles_in_play[cur_tile]['start'] = tile
			# update tile position
			cur_tile = self._getPosition(cur_tile, 1, direction)


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

		# no tiles or words in play
		if not self.tiles_in_play:
			valid_placements = self._getCreatableWords('7-7', self.letters_in_hand[player])
			if DEBUG: print valid_placements
			# get optimal words and points
			self._getOptimalPlacement(optimalMap, valid_placements, self.letters_in_hand[player])
		else:
			# check current tiles in play
			for tile in self.tiles_in_play:
				if not (self.tiles_in_play[tile][ACROSS] and self.tiles_in_play[tile][DOWN]):
					pivot = self.tiles_in_play[tile]['letter']
					possible_words = self.possible_words[pivot]
					for word in possible_words:
						if DEBUG: print 'checking tile: '+ str(tile) + ',  letter: '+str(pivot)
						if not self.tiles_in_play[tile][ACROSS]: direction = ACROSS
						else: direction = DOWN
						valid_placements = self._checkPlacement(pivot, word, tile, direction, self.letters_in_hand[player])
						if valid_placements:
							# get optimal words and points
							self._getOptimalPlacement(optimalMap, valid_placements, self.letters_in_hand[player])
			
			# check current words in play
			for word_played in self.words_in_play:
				word_dict = self.possible_words[self.words_in_play[word_played]['shortest']]
				word_list = []
				for word in word_dict:
					if word_played != word and word_played in word:
						word_list.append(word)
				# go through sub list of possible words
				for word in word_list:
					tile = self.words_in_play[word_played]['start']
					direction = self.words_in_play[word_played]['direction']
					valid_placements = self._checkPlacement(word_played, word, tile, direction, self.letters_in_hand[player])
					valid_sub_placements = []
					if valid_placements:
						for w, t, d, l in valid_placements:
							# if letters used == 1, check for additional possible words to make on new pivot
							if len(l) == 1:
								sub_pivot = l[0]
								if t in self.tiles_in_play: sub_tile = self._getPosition(t, len(w)-1, direction)
								else: sub_tile = t
								sub_direction = self._getOtherDirection(direction)
								sub_letters_in_hand = list(self.letters_in_hand[player])
								sub_letters_in_hand.remove(sub_pivot)
								sub_dict = self.possible_words[sub_pivot]
								for sub_word in sub_dict:
									sub_placements = self._checkPlacement(sub_pivot, sub_word, sub_tile, sub_direction, sub_letters_in_hand)
									if sub_placements:
										for sw, st, sd, sl in sub_placements:
											sl.extend(l)
											valid_sub_placements.append((sw, st, sd, sl))
						# add valid sub placements to placement list
						valid_placements.extend(valid_sub_placements)
						# get optimal words and points
						self._getOptimalPlacement(optimalMap, valid_placements, self.letters_in_hand[player])
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


	# find optimal placement
	def _getOptimalPlacement(self, optimalMap, valid_placements, letters_in_hand):
		for w, t, d, l in valid_placements:
			if (w, t, d, l) not in optimalMap['words']:
				l.sort()
				points = self._checkWordScore(letters_in_hand, w, t, d)
				if points > optimalMap['points']:
					del optimalMap['words'][:]
					optimalMap['words'].append((w, t, d, l))
					optimalMap['points'] = points
				elif points == optimalMap['points']:
					optimalMap['words'].append((w, t, d, l))


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


	# check whether word can be placed on the board
	def _checkPlacement(self, pivot, word, tile, direction, letters_in_hand):
		valid_placements = []
		other_direction = self._getOtherDirection(direction)

		# find position of each pivot in the word
		start_pos = 0
		end_pos = len(word)
		for i in range(0, word.count(pivot)):
			validPlacement = True
			letters_needed = []
			index = word.find(pivot, start_pos, end_pos)
			start_tile = self._getPosition(tile, 0-index, direction)

			# start of word exceeds board size, discard rest of the pivot checking
			if not start_tile: break

			# try and build the word around the pivot
			letter_pos = 0
			while letter_pos < len(word):
				# don't need to check pivot
				if letter_pos-index == 0:
					letter_pos += len(pivot)
					continue

				# check all other letters
				else:
					tile_pos = self._getPosition(tile, letter_pos-index, direction)
					if not tile_pos:
						# word too long; exceeds board size, break
						validPlacement = False
						break
					elif tile_pos in self.tiles_in_play and self.tiles_in_play[tile_pos]['letter'] != word[letter_pos]:
						# another letter already on the board, break
						validPlacement = False
						break
					else:
						# checking surrounding letters; check up if ACROSS, left if DOWN
						prev_word = ''
						prev_tile_pos = self._getPosition(tile_pos, -1, other_direction)
						if prev_tile_pos in self.tiles_in_play:
							if self.tiles_in_play[prev_tile_pos][other_direction]:
								prev_word = self.tiles_in_play[prev_tile_pos][other_direction]
							else:
								prev_word = self.tiles_in_play[prev_tile_pos]['letter']
						# checking surrounding letters; check down if ACROSS, right if DOWN
						next_word = ''
						next_tile_pos = self._getPosition(tile_pos, 1, other_direction)
						if next_tile_pos in self.tiles_in_play:
							if self.tiles_in_play[next_tile_pos][other_direction]:
								next_word += self.tiles_in_play[next_tile_pos][other_direction]
							else:
								next_word += self.tiles_in_play[next_tile_pos]['letter']
						# if surrounding letters exist, check if it makes valid word with current letter
						if prev_word or next_word:
							side_word = prev_word + word[letter_pos] + next_word
							if not self._checkWord(side_word):
								# side word is not valid, break
								validPlacement = False
								break
						# add current letter to letter check
						letters_needed.append(word[letter_pos])
					letter_pos += 1
			# tile placement is valid
			if validPlacement:
				# check if player has enough letters and if boundaries are clean
				letters_used = self._letterCheck(letters_needed, letters_in_hand)
				if letters_used and self._boundaryCheck(len(word), start_tile, direction):
					# word is good, add (word, tile, direction, letters_used) tuple to return
					valid_placements.append((word, start_tile, direction, letters_used))
			start_pos = index + 1
		return valid_placements


	# check whether word exists in dictionary
	def _checkWord(self, word):
		return word in self.dictionary


	# get other direction
	def _getOtherDirection(self, direction):
		if direction == ACROSS: return DOWN
		return ACROSS


	# check whether letter exists before and after word
	def _boundaryCheck(self, word_length, tile, direction):
		prev_pos = self._getPosition(tile, -1, direction)
		if prev_pos and prev_pos in self.tiles_in_play: return False
		next_pos = self._getPosition(tile, word_length, direction)
		if next_pos and next_pos in self.tiles_in_play: return False
		return True


	# find the score of a word placement
	def _checkWordScore(self, letters_in_hand, word, tile, direction):
		tmpletters = list(letters_in_hand)
		other_direction = self._getOtherDirection(direction)
		main_multiplier = 1
		main_points = side_points = bonus_points = 0
		for letter in word:
			# letter already exists on board, grab letter face value
			if tile in self.tiles_in_play:
				# ERROR: letter in word doesn't match letter on board (should have failed placement check)
				if self.tiles_in_play[tile]['letter'] != letter:
					return 0
				main_points += self.tiles_in_play[tile]['points']
				tile = self._getPosition(tile, 1, direction)
				continue

			# (TODO) have to choose blanks based on greedyness
			# get letter value, letter exists in hand
			if letter in tmpletters:
				current_letter_points = self.letters[letter]['points'] * self._getLetterMultiplier(tile)
				tmpletters.remove(letter)
			# use a blank letter tile
			elif 'blank' in tmpletters:
				current_letter_points = 0
				tmpletters.remove('blank')
			# ERROR: impossible to create word (should have failed placement check)
			else:
				return 0

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
		return self.letters_in_hand[player]


	# prettify current scrabble board and output
	def printBoard(self):
		output = '     '
		for col in range(0, self.board_size):
			output += str(col)
			if len(str(col)) == 1: output += '    '
			else: output += '   '
		print output + '\n'

		for row in range(0, self.board_size):
			for i in range (0, 2):
				if i == 0:
					output = str(row)
					if len(str(row)) == 1: output += '   |'
					else: output += '  |'
				else: output = '    |'
				for col in range(0, self.board_size):
					tile = str(row) + '-' + str(col)
					if i == 1: output += '____|'
					elif tile in self.tiles_in_play: output += self.tiles_in_play[tile]['letter'].upper() + '   |'
					elif tile in self.double_letter: output += '*   |'
					elif tile in self.triple_letter: output += '#   |'
					elif tile in self.double_word: output += 'x2  |'
					elif tile in self.triple_word: output += 'x3  |'
					else: output += '    |'
				print output


	# place a word onto the board
	# (TODO) add word placement function
	def placeWord(self, word, tile, direction):
		# check placement (check whether can place, and if user has enough letters)
		# check score
		# place word
		# get new tiles
		return


# (TODO) add user input shell capability
if __name__ == '__main__':
	scrabble = Scrabble()
	scrabble.printBoard()
	print 'letters: '+ str(scrabble.getLetters('player0'))
	print scrabble.getOptimalMove('player0')
