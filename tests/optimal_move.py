import os
import sys
sys.path.append('../bin')
from scrabble import Scrabble
CONFIG_DIR = './optimal_move_config'


# setup config and dictionary for each test suite
# grabs next optimal move and returns
def setup(name, path=CONFIG_DIR):
	config = os.path.join(path, name+'.conf')
	dic = os.path.join(path, name)
	scrabble = Scrabble(1, config, dic)
	return scrabble.getOptimalMove()

# empty board, with an empty dictionary
# should return 0 points
def empty_noPossibleWords():
	opt = setup('empty_noPossibleWords')
	assert opt['points'] == 0, opt['points']

# empty board, one possible word 'star'
# should start at center of board
def empty_fourLetterWord():
	opt = setup('empty_fourLetterWord')
	assert opt['points'] == 8, opt['points']
	assert len(opt['words']) == 1, len(opt['words'])
	w, t, d, l = opt['words'][0]
	assert w == 'star', w
	assert t == '7-7', t

# empty board, one possible word 'coffee'
# placement is crucial, test algo for detecting tile bonus
def empty_sixLetterWord():
	opt = setup('empty_sixLetterWord')
	assert opt['points'] == 34, opt['points']
	w, t, d, l = opt['words'][0]
	assert t == '7-3', t

# empty board, one possible word 'coffee' using a 'blank' for c
# should return three optimal placements
def empty_oneBlank():
	opt = setup('empty_oneBlank')
	assert opt['points'] == 24, opt['points']
	assert len(opt['words']) == 3, len(opt['words'])

# empty board, creating word using two 'blanks'
# should return two optimal placements
def empty_twoBlanks():
	opt = setup('empty_twoBlanks')
	assert opt['points'] == 22, opt['points']
	assert len(opt['words']) == 2, len(opt['words'])

# empty board, creating word 'testers'
# should return word score and 50 point bonus
def empty_sevenLetterBonus():
	opt = setup('empty_sevenLetterBonus')
	assert opt['points'] == 66, opt['points']

# possible word placement starts off the board
# no optimal move
def boundary_start():
	opt = setup('boundary_start')
	assert opt['points'] == 0, opt['points']

# possible word placement extends the edge of boar
# no optimal move
def boundary_end():
	opt = setup('boundary_end')
	assert opt['points'] == 0, opt['points']

# one word on the board, but no words possible
def one_noPossibleWords():
	opt = setup('one_noPossibleWords')
	assert opt['points'] == 0, opt['points']

# one word on the board, one possible word 'start'
def one_oneWord():
	opt = setup('one_oneWord')
	assert opt['points'] == 10, opt['points']

# one word on the board, two possible words 'start', 'stark'
# optimal placement returns 'stark'
def one_twoWords():
	opt = setup('one_twoWords')
	assert opt['points'] == 21, opt['points']
	w, t, d, l = opt['words'][0]
	assert t == '5-9', t

# one word on the board, two possible words 'zease' and 'zeasters'
# zeaster has a lower word score, but is the optimal move with 7 letter bonus
def one_twoWordsBonus():
	opt = setup('one_twoWordsBonus')
	assert opt['points'] == 84, opt['points']

# one word on board, possible word 'restart' appends to beginning of 'start'
def one_startOfWord():
	opt = setup('one_startOfWord')
	assert opt['points'] == 7, opt['points']

# one word on board, possible word 'starter' appends to end of 'start'
def one_endOfWord():
	opt = setup('one_endOfWord')
	assert opt['points'] == 7, opt['points']

# one word on board 'tarts', possible word 'stop' creates 'starts' and 'stop'
def one_doubleWordAtStart():
	opt = setup('one_doubleWordAtStart')
	assert opt['points'] == 18, opt['points']

# one word on board 'start', possible word 'stop' creates 'starts' and 'stop'
def one_doubleWordAtEnd():
	opt = setup('one_doubleWordAtEnd')
	assert opt['points'] == 18, opt['points']

# one possible word 'stops' with blank tile, choose blank tile first
def one_blankTileFirst():
	opt = setup('one_blankTileFirst')
	assert opt['points'] == 22, opt['points']

# one possible word 'stops' with blank tile, choose blank tile last
def one_blankTileLast():
	opt = setup('one_blankTileLast')
	assert opt['points'] == 20, opt['points']

# two words on the board
# possible word intersects one and runs alongside the other, but side words are invalid
def two_invalidIntersect():
	opt = setup('two_invalidIntersect')
	assert opt['points'] == 0, opt['points']

# two words on the board
# possible word intersects one and runs alongside the other, and all side words are valid
def two_validIntersect():
	opt = setup('two_validIntersect')
	assert opt['points'] == 7, opt['points']

# two words on the board 'st[a]rt' '[s]top'
# possible word intersects both words through the middle 'pl[a]nk[s]'
def two_intersectBoth():
	opt = setup('two_intersectBoth')
	assert opt['points'] == 28, opt['points']

# two words on the board 'the' 'ore'
# possible word fits in between two existing words, 'therefore'
def two_betweenWords():
	opt = setup('two_betweenWords')
	assert opt['points'] == 15, opt['points']

# two words on the board 'there' 'ore'
# possible word 'life' fits in between and creates 'therefore'
def two_betweenWordsOneLetter():
	opt = setup('two_betweenWordsOneLetter')
	assert opt['points'] == 44, opt['points']

# two words on the board 'here' or'
# possible word uses both words to create a larger word, 'therefore'
def two_bothWords():
	opt = setup('two_bothWords')
	assert opt['points'] == 15, opt['points']

# two words on the board, 'animal' 'tar'
# possible word appends to end of one and start of another, 'animals' 'stars' 'tar'
def two_startOneEndSecond():
	opt = setup('two_startOneEndSecond')
	assert opt['points'] == 39, opt['points']

# two words on the board, 'animal' 'tar'
# possible word appends to end of one and start of another, 'animal[s]' '[s]tars' 'star', blank tile in brackets
def two_startOneEndSecondBlankFirst():
	opt = setup('two_startOneEndSecondBlankFirst')
	assert opt['points'] == 35, opt['points']

# two words on the board, 'animal' 'tar'
# possible word appends to end of one and start of another, 'animals' 'star[s]' '[s]tar', blank tile in brackets
def two_startOneEndSecondBlankLast():
	opt = setup('two_startOneEndSecondBlankLast')
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

