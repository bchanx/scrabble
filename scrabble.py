import os
import sys
import shutil
import random
import ConfigParser

config_dir = './config'
config_file = os.path.join(config_dir, 'scrabble.conf')
dictionary_file = os.path.join(config_dir, 'basic_english_word_list')
global_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'blank']
debug = False

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
		self.triple_word = config.get('init', 'triple_word').split('/')

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
		self.tiles_in_play = {}
		words_in_play = config.get('init', 'words_in_play')
		if words_in_play:
			words_and_position = words_in_play.split('/')
			for words in words_and_position:
				word, tile, direction = words.split(';')
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


	# get other direction
	def _getOtherDirection(self, direction):
		if direction == 'across':
			return 'down'
		return 'across'


	# check whether words can be placed on the board
	def _checkWordPlacement(self, list_of_words, tile):
		# TODO: case if board is entirely empty
		valid_words = []
		pivot = self.tiles_in_play[tile]['letter']
		if not self.tiles_in_play[tile]['across']:
			direction = 'across'
		else:
			direction = 'down'
		other_direction = self._getOtherDirection(direction)

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
							prev_word = ''
							# check up if 'across', left if 'down'
							prev_tile_pos = self._getPosition(tile_pos, -1, other_direction)
							if prev_tile_pos in self.tiles_in_play:
								if self.tiles_in_play[prev_tile_pos][other_direction]:
									prev_word = self.tiles_in_play[prev_tile_pos][other_direction]
								else:
									prev_word = self.tiles_in_play[prev_tile_pos]['letter']

							# check down if 'across', right if 'down'
							next_word = ''
							next_tile_pos = self._getPosition(tile_pos, 1, other_direction)
							if next_tile_pos in self.tiles_in_play:
								if self.tiles_in_play[next_tile_pos][other_direction]:
									next_word += self.tiles_in_play[next_tile_pos][other_direction]
								else:
									next_word += self.tiles_in_play[next_tile_pos]['letter']

							# check if side_word is a valid word
							if prev_word or next_word:
								side_word = prev_word + word[letter_pos] + next_word
								if not self._checkWord(side_word):
									# SIDE WORD IS NOT A VALID WORD, BREAK
									validWord = False
									break
				# word is valid, add (word, tile, direction) tuple to return list
				if validWord:
					valid_words.append((word, start_tile, direction))
				start_pos = index + 1
		return valid_words


	# return letter multiplier
	def _getLetterMultiplier(self, tile):
		if tile in self.double_letter:
			return 2
		elif tile in self.triple_letter:
			return 3
		return 1


	# return word multiplier
	def _getWordMultiplier(self, tile):
		if tile in self.double_word:
			return 2
		elif tile in self.triple_word:
			return 3
		return 1


	# return raw tile scores in a direction
	def _getRawTileScore(self, tile, length, direction):
		raw_tile_score = 0
		while tile in self.tiles_in_play:
			raw_tile_score += self.tiles_in_play[tile]['points']
			tile = self._getPosition(tile, length, direction)
		return raw_tile_score


	# find the score of a word placement
	def _checkWordScore(self, letters_in_hand, word, tile, direction):
		tmpletters = list(letters_in_hand)
		other_direction = self._getOtherDirection(direction)
		main_points = 0
		side_points = 0
		bonus_points = 0
		main_multiplier = 1
		for letter in word:
			# letter already on board, just get letter value
			if tile in self.tiles_in_play:
				if self.tiles_in_play[tile]['letter'] != letter:
					# letter does not match, ERROR FROM WORD CHECK
					return 0
				main_points += self.tiles_in_play[tile]['points']
				tile = self._getPosition(tile, 1, direction)
				continue

			# get current letter value from hand
			if letter in tmpletters:
				current_letter_points = self.letters[letter]['points'] * self._getLetterMultiplier(tile)
				tmpletters.remove(letter)
			else:
				if 'blank' in tmpletters:
					current_letter_points = 0
					tmpletters.remove('blank')
				else:
					# can't create word, ERROR FROM WORD CHECK
					return 0

			# current tile multiplier
			current_multiplier = self._getWordMultiplier(tile)

			# update main_multiplier
			main_multiplier *= current_multiplier

			# get side points
			current_side_points = 0
			prev_tile_pos = self._getPosition(tile, -1, other_direction)
			next_tile_pos = self._getPosition(tile, 1, other_direction)
			if prev_tile_pos in self.tiles_in_play or next_tile_pos in self.tiles_in_play:
				current_side_points += self._getRawTileScore(prev_tile_pos, -1, other_direction)
				current_side_points += self._getRawTileScore(next_tile_pos, 1, other_direction)
				current_side_points += current_letter_points
				side_points += current_side_points * current_multiplier

			# get main_points
			main_points += current_letter_points

			# update tile pos
			tile = self._getPosition(tile, 1, direction)

		# apply main multiplier to main points
		main_points *= main_multiplier

		# 7 letters used, 50 point bonus!
		if len(letters_in_hand) == 7 and len(tmpletters) == 0:
			bonus_points = 50

		# return summation of points
		return main_points + side_points + bonus_points


	# find best possible word player can create on a tile
	def _findMostPoints(self, letters_in_hand, tile):
		bestWords = []
		mostPoints = 0

		possible_words = self._findPossibleWords(list(letters_in_hand), self.tiles_in_play[tile]['letter'])
		if debug: print 'pivot: '+str(self.tiles_in_play[tile]['letter']) + '  at: '+str(tile)+'  '+str( possible_words )
		valid_words = self._checkWordPlacement(possible_words, tile)
		if debug: print '   valid_words: ' + str(valid_words)

		for w, t, d in valid_words:
			points = self._checkWordScore(letters_in_hand, w, t, d)
			if debug: print 'word: '+str(w)+',  points: ' + str(points)
			if points > mostPoints:
				del bestWords[:]
				bestWords.append((w, t, d))
				mostPoints = points
			elif points == mostPoints:
				bestWords.append((w, t, d))

		return (mostPoints, bestWords)


	# get next optimal move
	def findOptimal(self, player):
		bestWords = []
		mostPoints = 0
		for tile in self.tiles_in_play:
			if not (self.tiles_in_play[tile]['across'] and self.tiles_in_play[tile]['down']):
				points, words = self._findMostPoints(self.letters_in_hand[player], tile)
				if points > mostPoints:
					del bestWords[:]
					bestWords.extend(words)
					mostPoints = points
				elif points == mostPoints:
					bestWords.extend(words)
		print '=== MOST POINTS: '+str(mostPoints)+' === ' + str(bestWords)
		return bestWords


	# prettify current scrabble board and output
	def printBoard(self):
		for row in range(0, self.board_size):
			output = '|'
			for col in range(0, self.board_size):
				tile = str(row) + '-' + str(col)
				if tile in self.tiles_in_play:
					output = output + self.tiles_in_play[tile]['letter'] + ' |'
				elif tile in self.double_letter:
					output = output + '* |'
				elif tile in self.triple_letter:
					output = output + '# |'
				elif tile in self.double_word:
					output = output + 'x2|'
				elif tile in self.triple_word:
					output = output + 'x3|'
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
