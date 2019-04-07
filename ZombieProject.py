import pygame

from random import randint, choice
from time import sleep

from pygame.locals import *

pygame.init()


def readCityFile(filename):

	# start by reading a tab separated value file (tsv) that holds a random city map
	# a file like this can be generated from from https://donjon.bin.sh/d20/dungeon/
	file = open(filename)
	data = file.read()
	file.close()

	# these files are a bit unusual because the tab character is used as a delimiter
	# but if there is nothing but a wal at a given location, no character is placed
	# between adjacent delimiters - this makes processing a bit trickier...

	# first split the data into lines
	data = data.split("\n")

	# width will hold the width of the street (i.e., how many "people" wide?)
	width = 3

	# start with an empty list of lists of Booleans (i.e., "solid" or "not solid")
	map = []

	# read a line from the file...
	for line in data:

		# ...and build up the corresponding row, one "cell" at a time
		row = []
		
		# start by assuming there is nothing but a solid wall there...
		solid = True
		for char in line:
		
			# ...but if you find a character OTHER THAN tab it won't be solid...
			if char != "\t":
				solid = False
			else:
			
				# ...at each tab (i.e., delimiter) add "solid" or "not solid" to row
				# (doing it three times makes your streets have a width of three)
				for i in range(width):
					row.append(solid)
				
				# then reset your solid variable and look at the next character
				solid = True
				
		# because we stripped the newline character we have to add in the right wall
		for i in range(width):
			row.append(solid)
			
		# same; doing it three times makes your streets have a width of three
		for i in range(width):
			map.append(row)

	# transpose (because donjon makes rectangular maps) and return
	return [list(i) for i in zip(*map)]

	
def makeCityImage(map, zoom):

	rows = len(map)
	cols = len(map[0])
	wide = cols*zoom
	high = rows*zoom

	# make a new surface with a dimensions that are sufficient to hold the map
	surface = pygame.Surface((wide, high))
	
	# then make a pixel array of it 
	pxarray = pygame.PixelArray(surface)
	
	# you could also use set_at to accomplish this, but pixel arrays are faster
	for x in range(wide):
		for y in range(high):
			if map[y//zoom][x//zoom]:
				pxarray[x, y] = 0x7F7F7F	
			else:
				pxarray[x, y] = 0x202020
	
	# delete the pixel array when you are done
	del pxarray
	
	return surface, wide, high
			
			
def getRandomDirection():
	# choose a random direction
	return choice([[-1, 0], [0, 1], [1, 0], [0, -1]])

	
def makeInitialPopulations(map):

	rows = len(map)
	cols = len(map[0])
	
	humans = []
	while len(humans) < 500:
	
		while True:
		
			row = randint(0, rows-1)
			col = randint(0, cols-1)
			direction = getRandomDirection()
			
			if map[row][col] == False:
				humans.append([row, col, direction, "ROAM"])
				break

	zombis = []
	while len(zombis) < 1:
	
		while True:
		
			row = randint(0, rows-1)
			col = randint(0, cols-1)
			direction = getRandomDirection()
			
			if map[row][col] == False:
				zombis.append([row, col, direction, "ROAM"])
				break
				
	return humans, zombis

			
def getNearest(agent, others):

	nearby = []
	
	# consider everyone in the other population and make a tuple of that entity
	# and its distance from the agent; this is an easy way to find the nearest
	# member of the other population
	for other in others:
		nearby.append([abs(other[0] - agent[0]) + abs(other[1] - agent[1]), other])

	nearest = min(nearby)
	
	return nearest


def perceive(map, humans, zombis):	

	# complete the "perception" phase for each human
	for human in humans:

		# find the nearest zombie
		nearestZombi = getNearest(human, zombis)

		# if the nearest zombie is on the same cell as this human...
		if (nearestZombi[0] == 0):
		
			# ... GAME OVER, MAN!
			human[3] = 'DEAD'

		# if the nearest zombie is within a (Manhattan) distance of 20...
		elif (nearestZombi[0] < 5):
		
			# ...then it is time to panic
			human[3] = 'FLEE'
			
			possible_directions = []
		
			# determine whether or not the zombi is above or below...
			nearestIsBelow = nearestZombi[1][0] > human[0]

			if nearestIsBelow:
				possible_directions.append([1, 0])
			else:
				possible_directions.append([-1, 0])
			
			# ...and to the left or the right, and change direction...
			nearestIsRight = nearestZombi[1][1] > human[1]
			if nearestIsRight:
				possible_directions.append([0, 1])
			else:
				possible_directions.append([0, -1])
				
			chosen_direction = choice(possible_directions)
			human[2][0] = chosen_direction[0]
			human[2][1] = chosen_direction[1]
		

		else:
		
			# with no zombies nearby, the human goes back to roaming
			human[3] = 'ROAM'
		
		
	# complete the "perception" phase for each zombi
	for zombi in zombis:

		# find the nearest zombie
		nearestHuman = getNearest(zombi, humans)

		# if the nearest zombie is within a (Manhattan) distance of 20...
		if (nearestHuman[0] < 5):
		
			# ...then it is time to hunt
			zombi[3] = 'HUNT'
			
			possible_directions = []
			
			# determine whether or not the human is above or below...
			nearestIsBelow = nearestHuman[1][0] > zombi[0]

			if nearestIsBelow:
				possible_directions.append([1, 0])
			else:
				possible_directions.append([-1, 0])
			
			# ...and to the left or the right, and change direction...
			nearestIsRight = nearestHuman[1][1] > zombi[1]
			if nearestIsRight:
				possible_directions.append([0, 1])
			else:
				possible_directions.append([0, -1])
		
			chosen_direction = choice(possible_directions)
			zombi[2][0] = chosen_direction[0]
			zombi[2][1] = chosen_direction[1]
			
		else:
		
			# with no humans nearby, the zombi goes back to roaming
			zombi[3] = 'ROAM'
			
	return humans, zombis
	
	
def act(map, humans, zombis):

	# complete the "action" phase for each human
	for human in humans:

		# make sure no human is trying to walk into a wall...
		while map[human[0] + human[2][0]][human[1] + human[2][1]]:
			# ...and keep choosing a random direction until they are not
			human[2] = choice([[-1, 0], [0, 1], [1, 0], [0, -1]])

		# if the human is currently in the "ROAM" state
		if human[3] == 'ROAM':
		
			randomvalue = randint(0, 100)
			
			# 10% of the time, this human chooses a random direction
			if randomvalue < 10:
				human[2] = choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
			# 60% of the time, this human moves in the desired direction
			elif randomvalue < 70:
				human[0] += human[2][0]
				human[1] += human[2][1]
			# 30% (i.e., the rest) of the time, this human does nothing
			else:
				pass # this is Python's special word for "do nothing"

		# if the human is currently in the "FLEE" state
		elif human[3] == 'FLEE':

			# 100% of the time, this human runs from the nearest zombi
			human[0] += human[2][0]
			human[1] += human[2][1]
			

	# complete the "action" phase for each zombi
	for zombi in zombis:

		# make sure no zombi is trying to walk into a wall...
		while map[zombi[0] + zombi[2][0]][zombi[1] + zombi[2][1]]:
			# ...and keep choosing a random direction until they are not
			zombi[2] = choice([[-1, 0], [0, 1], [1, 0], [0, -1]])

		# if the human is currently in the "ROAM" state
		if zombi[3] == 'ROAM':
		
			randomvalue = randint(0, 100)
			
			# 10% of the time, this zombi chooses a random direction
			if randomvalue < 10:
				zombi[2] = choice([[-1, 0], [0, 1], [1, 0], [0, -1]])
			# 90% (i.e., the rest) of the time, this zombi moves
			else:
				zombi[0] += zombi[2][0]
				zombi[1] += zombi[2][1]

		# if the human is currently in the "FLEE" state
		elif zombi[3] == 'HUNT':

			# 100% of the time, this human runs from the nearest zombi
			zombi[0] += zombi[2][0]
			zombi[1] += zombi[2][1]

	return humans, zombis

	
def renderScene(zoom_factor, humans, zombis):

	global win_surf
	global img_city	

	# draw the city map
	win_surf.blit(img_city, (0, 0))

	# draw every human
	for human in humans:
		if human[3] == 'FLEE':
			draw_colour = (245, 255, 250) # mint cream
		else:
			draw_colour = (233, 150, 122) # dark salmon
		pygame.draw.rect(win_surf, draw_colour, (human[1]*zoom_factor, human[0]*zoom_factor, zoom_factor, zoom_factor))
		
	# draw every zombi
	for zombi in zombis:
		if zombi[3] == 'HUNT':
			draw_colour = (124, 252, 0)
		else:
			draw_colour = (152, 251, 152)
		pygame.draw.rect(win_surf, draw_colour, (zombi[1]*zoom_factor, zombi[0]*zoom_factor, zoom_factor, zoom_factor))

	# update after drawing
	pygame.display.update()
	
		
def main():

	global win_wide
	global win_high
	global win_surf
	global img_city
	
	zoom_factor = 5

	map = readCityFile("donjon_city_data.txt")

	humans, zombis = makeInitialPopulations(map)
	
	img_city, win_wide, win_high = makeCityImage(map, zoom_factor)

	win_surf = pygame.display.set_mode((win_wide, win_high))
	
	closed_flag = False
	while not closed_flag:

		for event in pygame.event.get():
			if event.type == QUIT:
				closed_flag = True
		
		if len(humans) > 0:

			humans, zombis = perceive(map, humans, zombis)

			humans, zombis = act(map, humans, zombis)
			
			for i in range(len(humans)-1, -1, -1):
			
				if humans[i][3] == 'DEAD':
					humans[i][3] == 'ROAM'
					zombis.insert(0, humans.pop(i))
					
			renderScene(zoom_factor, humans, zombis)
			
			pygame.time.delay(5)
			

			
main()