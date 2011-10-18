import os
import sys
import ConfigParser
sys.path.append('../bin')
from scrabble import Scrabble
CONFIG_FILE = './test_config/optimal_move.conf'
WORD_DICT = './test_config/optimal_move'

config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)

# setup config and dictionary for each test suite
# grabs next optimal move and returns
def setup(words_in_play, letters_in_hand, word_list):
	# setup words_in_play and tiles_in_hand
	config.set('init', 'words_in_play', words_in_play)
	config.set('letters_in_hand', 'player0', letters_in_hand)
	with open(CONFIG_FILE, 'w') as config_file:
		config.write(config_file)
	# setup dictionary
	with open(WORD_DICT, 'w') as word_dict:
		for word in word_list:
			word_dict.write(word+'\n')
	scrabble = Scrabble(1, CONFIG_FILE, WORD_DICT)
	return scrabble.getOptimalMove()

# empty board, with an empty dictionary
# should return 0 points
def empty_noPossibleWords():
	opt = setup('', 'a/b/c/d/e/f/g', [])
	assert opt['points'] == 0, opt['points']

# empty board, one possible word 'star'
# should start at center of board
def empty_fourLetterWord():
	opt = setup('', 's/t/a/r', ['star'])
	assert opt['points'] == 8, opt['points']
	assert len(opt['words']) == 1, len(opt['words'])
	w, t, d, l = opt['words'][0]
	assert w == 'star', w
	assert t == '7-7', t

# empty board, one possible word 'coffee'
# placement is crucial, test algo for detecting tile bonus
def empty_sixLetterWord():
	opt = setup('', 'c/o/f/f/e/e', ['coffee'])
	assert opt['points'] == 34, opt['points']
	w, t, d, l = opt['words'][0]
	assert t == '7-3', t

# empty board, one possible word 'coffee' using a 'blank' for c
# should return three optimal placements
def empty_oneBlank():
	opt = setup('', 'blank/o/f/f/e/e', ['coffee'])
	assert opt['points'] == 24, opt['points']
	assert len(opt['words']) == 3, len(opt['words'])

# empty board, creating word using two 'blanks'
# should return two optimal placements
def empty_twoBlanks():
	opt = setup('', 'blank/blank/f/f/e/e', ['coffee'])
	assert opt['points'] == 22, opt['points']
	assert len(opt['words']) == 2, len(opt['words'])

# empty board, creating word 'testers'
# should return word score and 50 point bonus
def empty_sevenLetterBonus():
	opt = setup('', 't/e/s/t/e/r/s', ['testers'])
	assert opt['points'] == 66, opt['points']

# possible word placement starts off the board
# no optimal move
def boundary_start():
	opt = setup('animals;7-1;across/start;5-1;down', 'e/a', ['eat'])
	assert opt['points'] == 0, opt['points']

# possible word placement extends the edge of boar
# no optimal move
def boundary_end():
	opt = setup('animals;7-7;across/start;7-13;down', 'e/a', ['tea'])
	assert opt['points'] == 0, opt['points']

# one word on the board, but no words possible
def one_noPossibleWords():
	opt = setup('start;7-7;across', 's/t/a/r/t/x/y', [])
	assert opt['points'] == 0, opt['points']

# one word on the board, one possible word 'start'
def one_oneWord():
	opt = setup('start;7-7;across', 's/t/a/r/t', ['start'])
	assert opt['points'] == 10, opt['points']

# one word on the board, two possible words 'start', 'stark'
# optimal placement returns 'stark'
def one_twoWords():
	opt = setup('start;7-7;across', 's/t/a/r/t/k', ['start', 'stark'])
	assert opt['points'] == 21, opt['points']
	w, t, d, l = opt['words'][0]
	assert t == '5-9', t

# one word on the board, two possible words 'zease' and 'zeasters'
# zeaster has a lower word score, but is the optimal move with 7 letter bonus
def one_twoWordsBonus():
	opt = setup('start;7-7;across', 'z/e/a/s/e/r/s', ['zease', 'zeasters'])
	assert opt['points'] == 84, opt['points']

# one word on board, possible word 'restart' appends to beginning of 'start'
def one_startOfWord():
	opt = setup('start;7-7;across', 'r/e', ['restart'])
	assert opt['points'] == 7, opt['points']

# one word on board, possible word 'starter' appends to end of 'start'
def one_endOfWord():
	opt = setup('start;7-7;across', 'e/r', ['starter'])
	assert opt['points'] == 7, opt['points']

# one word on board 'tarts', possible word 'stop' creates 'starts' and 'stop'
def one_doubleWordAtStart():
	opt = setup('tarts;7-5;across', 's/t/o/p', ['stop', 'starts'])
	assert opt['points'] == 18, opt['points']

# one word on board 'start', possible word 'stop' creates 'starts' and 'stop'
def one_doubleWordAtEnd():
	opt = setup('start;7-5;across', 's/t/o/p', ['stop', 'starts'])
	assert opt['points'] == 18, opt['points']

# one possible word 'stops' with blank tile, choose blank tile first
def one_blankTileFirst():
	opt = setup('star;3-7;across', 's/t/o/p/blank', ['stops', 'stars'])
	assert opt['points'] == 22, opt['points']

# one possible word 'stops' with blank tile, choose blank tile last
def one_blankTileLast():
	opt = setup('star;7-7;across', 's/t/o/p/blank', ['stops', 'stars'])
	assert opt['points'] == 20, opt['points']

# two words on the board
# possible word intersects one and runs alongside the other, but side words are invalid
def two_invalidIntersect():
	opt = setup('start;7-7;across/stop;6-11;down', 'a/t', ['art'])
	assert opt['points'] == 0, opt['points']

# two words on the board
# possible word intersects one and runs alongside the other, and all side words are valid
def two_validIntersect():
	opt = setup('start;7-7;across/stop;6-11;down', 'a/t', ['art', 'as', 'to'])
	assert opt['points'] == 7, opt['points']

# two words on the board 'st[a]rt' '[s]top'
# possible word intersects both words through the middle 'pl[a]nk[s]'
def two_intersectBoth():
	opt = setup('start;7-7;across/stop;10-9;across', 'p/l/n/k', ['planks'])
	assert opt['points'] == 28, opt['points']

# two words on the board 'the' 'ore'
# possible word fits in between two existing words, 'therefore'
def two_betweenWords():
	opt = setup('the;7-1;across/ore;7-7;across', 'r/e/f', ['therefore'])
	assert opt['points'] == 15, opt['points']

# two words on the board 'there' 'ore'
# possible word 'life' fits in between and creates 'therefore'
def two_betweenWordsOneLetter():
	opt = setup('there;7-2;across/ore;7-8;across', 'l/i/f/e/blank', ['life', 'therefore'])
	assert opt['points'] == 44, opt['points']

# two words on the board 'here' or'
# possible word uses both words to create a larger word, 'therefore'
def two_bothWords():
	opt = setup('here;7-2;across/or;7-7;across', 't/f/e', ['therefore'])
	assert opt['points'] == 15, opt['points']

# two words on the board, 'animal' 'tar'
# possible word appends to end of one and start of another, 'animals' 'stars' 'tar'
def two_startOneEndSecond():
	opt = setup('animal;10-1;across/tar;14-8;across', 's/t/a/r/s', ['animals', 'star', 'stars'])
	assert opt['points'] == 39, opt['points']

# two words on the board, 'animal' 'tar'
# possible word appends to end of one and start of another, 'animal[s]' '[s]tars' 'star', blank tile in brackets
def two_startOneEndSecondBlankFirst():
	opt = setup('animal;10-1;across/tar;14-8;across', 's/t/a/r/blank', ['animals', 'star', 'stars'])
	assert opt['points'] == 35, opt['points']

# two words on the board, 'animal' 'tar'
# possible word appends to end of one and start of another, 'animals' 'star[s]' '[s]tar', blank tile in brackets
def two_startOneEndSecondBlankLast():
	opt = setup('animal;0-1;across/tar;4-8;across', 's/t/a/r/blank', ['animals', 'star', 'stars'])
	assert opt['points'] == 45, opt['points']


if __name__ == '__main__':
	empty_noPossibleWords()
	empty_fourLetterWord()
	empty_sixLetterWord()
	empty_oneBlank()
	empty_twoBlanks()
	empty_sevenLetterBonus()
	boundary_start()
	boundary_end()
	one_noPossibleWords()
	one_oneWord()
	one_twoWords()
	one_twoWordsBonus()
	one_startOfWord()
	one_endOfWord()
	one_blankTileFirst()
	one_blankTileLast()
	one_doubleWordAtStart()
	one_doubleWordAtEnd()
	two_invalidIntersect()
	two_validIntersect()
	two_intersectBoth()
	two_betweenWords()
	two_betweenWordsOneLetter()
	two_bothWords()
	two_startOneEndSecond()
	two_startOneEndSecondBlankFirst()
	two_startOneEndSecondBlankLast()

