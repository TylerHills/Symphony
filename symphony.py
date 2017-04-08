import discord
from discord.ext.commands import Bot
import json
import sys
import datetime
from shapely.geometry import Point, MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.ops import cascaded_union
import atexit

symphony = Bot(command_prefix = "!")
server = "unnasigned"
pokemonList = {}
moveList = {}
geoDataDict = {}
symphonyUsers = []

#channels
input = discord.Object(id = '288563630645968896')
northSeattle = discord.Object(id = '288537029514362880')
centralSeattle = discord.Object(id = '288537058127904768')
southSeattle = discord.Object(id = '288537105645174784')
upperEast = discord.Object(id = '288537161748447232')
lowerEast = discord.Object(id = '288537231977873409')
perfectIV = discord.Object(id = '288537263627829248')
all = discord.Object(id = '297541247378391042')
dratini = discord.Object(id = '298239380857028611')
larvitar = discord.Object(id = '298239647929204738')
rares = discord.Object(id = '298240115812073472') #snorlax-chancey-lapras


class Spawn:
	def __init__(self):
		self.pokemon_id = ""
		self.move_1 = ""
		self.move_2 = ""
		self.gender = ""
		self.shiny = False
		self.cp = 0
				
		self.individual_attack = ""
		self.individual_defense = ""
		self.individual_stamina = ""
		self.ivTotal = 0
		
		self.longitude = 0
		self.latitude = 0
		
		self.seconds_until_despawn = 0
		
		self.message = ""
		self.pokemonName = ""
		self.move1Name = ""
		self.move2Name = ""
		self.sprite = ""
		self.percent = 0
		self.expireTime = ""
		self.link = ""
		self.remainingTime = ""
		self.locationName = ""
		self.region =  ""
		
	def calculatePercent(self):
		self.ivTotal = self.individual_attack + self.individual_defense + self.individual_stamina
		p = self.ivTotal / 45
		p = p * 100
		self.percent = round(p, 1)
		
	def getNames(self):
		self.pokemonName = pokemonList[str(self.pokemon_id)]["name"]
		try:
			self.move1Name = moveList[str(self.move_1)]["name"]
			self.move2Name = moveList[str(self.move_2)]["name"]
		except:
			print("Error retreiving move name at: " + datetime.datetime.now().strftime('%m/%d/%y %I:%M:%S %p'))
		
		if self.gender == 1: self.gender = '♀'
		else: self.gender = '♂'
		
		et = (datetime.datetime.now() + datetime.timedelta(seconds = self.seconds_until_despawn)).time()
		self.expireTime = et.strftime('%H:%M:%S')
		
		hours, remainder = divmod(self.seconds_until_despawn, 3600)
		minutes, seconds = divmod(remainder, 60)
		self.remainingTime = '%sm %ss' % (minutes, seconds)
		
		self.link = "http://maps.google.com/maps?q="+ str(self.latitude) + "," + str(self.longitude)
		
		self.locationName = findNeighborhood([self.longitude, self.latitude])
		
	def buildMessage(self):		
		title = self.pokemonName + " " + self.gender + " " + str(self.percent) + "% (" + str(self.individual_attack) + "/" + str(self.individual_defense) + "/" + str(self.individual_stamina) + ")"
		description = self.locationName.title() + "\n" + str(self.move1Name) + ", " + str(self.move2Name) + "\n" + "Until " + self.expireTime + " (" + self.remainingTime + ")"
		
		if self.percent > 99: ivColor = discord.Color.orange()
		elif self.percent > 90: ivColor = discord.Color.purple()
		elif self.percent > 80: ivColor = discord.Color.blue()
		elif self.percent > 50: ivColor = discord.Color.green()
		elif self.percent > 25: ivColor = discord.Color(0xffffff)
		else: ivColor = discord.Color.light_grey()
		
		self.message = discord.Embed(title = title, color = ivColor, url = self.link, description = description)
		self.message.set_thumbnail(url="https://raw.githubusercontent.com/kvangent/PokeAlarm/master/icons/" + str(self.pokemon_id) +  ".png")

class SymphonyUser:
	def __init__(self, name_, id_, discriminator_, subscriptions_):
		self.name = name_
		self.id = id_
		self.discriminator = discriminator_
		self.subscriptions = subscriptions_
		self.filters = {}
		self.customerFilter = False

def exit_handler():
	f = open('onClose.txt', 'w')
	f.write('Closing text here')
	f.close()
	print("CLOSING DO STUFF HERE")

	
def exportUsers():
	print("Exporting users")
	userData = json.dumps([symphonyUser.__dict__ for symphonyUser in symphonyUsers])

	f = open('users.json', 'w')
	f.write(userData)
	f.close()
	
def importUsers():
	global symphonyUsers
	print("Importing Users")
	with open("users.json", "r", encoding='utf-8') as data_file:   
		userData = json.load(data_file)
		print(userData)
	
	for symphonyUser in userData: 
		print(symphonyUser["name"])
		print(symphonyUser["id"])
		print(symphonyUser["subscriptions"])
		su = SymphonyUser(symphonyUser["name"], symphonyUser["id"], symphonyUser["discriminator"], symphonyUser["subscriptions"])
		symphonyUsers.append(su)
	print("Users Imported")
	
def findNeighborhood(pointCoords):
	point = Point(pointCoords)
	for label, shape in geoDataDict.items():
		if (shape.contains(point)):
			return label
	print("Neighborhood not found at: " + datetime.datetime.now().strftime('%m/%d/%y %I:%M:%S %p'))
	return "Neighborhood not found"
		
def loadPokemon():
	with open("pokemon.json") as data_file:    
		data = json.load(data_file)	
	return data

def loadMoves():
	with open("moves.json") as data_file:    
		data = json.load(data_file)	
	return data

def loadDataFromJson(fileName):
	with open(fileName, "r", encoding='utf-8') as data_file:    
		data = json.load(data_file)
	return data

def createShape(shapeData):
	areaLabel = shapeData["properties"]["label"]
	shapeType = shapeData["geometry"]["type"]
	if (shapeType == "Polygon"):
		shapeCoords = shapeData["geometry"]["coordinates"][0]
		shape = Polygon(shapeCoords)
	else: #shapeType == "MultiPolygon"
		shapeCoords = shapeData["geometry"]["coordinates"]
		preppedcoords = PrepCoordsForShapely(shapeCoords)
		shape = MultiPolygon(*preppedcoords)
	
	if (areaLabel in geoDataDict):
		existingShape = geoDataDict[areaLabel]
		shapesToMerge = [existingShape, shape]
		shape = cascaded_union(shapesToMerge)
	
	return shape

def loadGeoData():
	northGeoJSON = loadDataFromJson("north.geoJSON")
	southGeoJSON = loadDataFromJson("south.geoJSON")
	
	regions = [northGeoJSON, southGeoJSON]
	
	for region in regions:
		for area in region["features"]:
			areaLabel = area["properties"]["label"]
			shape = createShape(area)
			geoDataDict[areaLabel.lower()] = shape

# preps geoJSON coords to create shapely multipolygon
# http://gis.stackexchange.com/questions/70591/creating-shapely-multipolygons-from-shapefile-multipolygons
def PrepCoordsForShapely(rawcoords):
    preppedcoords = []
    #according to the geojson specs, a multipolygon is a list of linear rings, so we loop each
    for eachpolygon in rawcoords:
        #the first linear ring is the coordinates of the polygon, and shapely needs it to be a tuple
        tupleofcoords = tuple(eachpolygon[0])
        #the remaining linear rings, if any, are the coordinates of inner holes, and shapely needs these to be nested in a list
        if len(eachpolygon) > 1:
            listofholes = list(eachpolygon[1:])
        else:
            listofholes = []
        #shapely defines each polygon in a multipolygon with the polygoon coordinates and the list of holes nested inside a tuple
        eachpreppedpolygon = (tupleofcoords, listofholes)
        #so append each prepped polygon to the final multipolygon list
        preppedcoords.append(eachpreppedpolygon)
    #finally, the prepped coordinates need to be nested inside a list in order to be used as a star-argument for the MultiPolygon constructor.
    return [preppedcoords]
	
def readInput(spawnData):
	s = Spawn()
	sd = json.loads(spawnData)
	s.pokemon_id = sd["pokemon_id"]
	s.move_1 = sd["move_1"]
	s.move_2 = sd["move_2"]
	#if (sd["shiny"] == 'true'): s.shiny = True
	s.individual_attack = sd["individual_attack"]
	s.individual_defense = sd["individual_defense"]
	s.individual_stamina = sd["individual_stamina"]
	s.longitude = sd["longitude"]
	s.latitude = sd["latitude"]
	s.seconds_until_despawn = sd["seconds_until_despawn"]
	s.getNames()
	s.calculatePercent()
	s.buildMessage()
	
	return s

def findSubcribedUsers(neighborhood):
	subscribedUsers = []
	for user in symphonyUsers:
		#print(user.name)
		#print(user.subscriptions)
		#print(neighborhood in user.subscriptions)
		if neighborhood in user.subscriptions: subscribedUsers.append(user)
	#print(len(subscribedUsers))
	return subscribedUsers
	
def isNeighborhoodInternal(neighborhood):
	neighborhood = neighborhood.strip()
	return neighborhood.lower() in geoDataDict

def subscribeLogic(ctx):
	message = ctx.message
	messageSanitized = message.content.replace("!subscribe ", "")
	messageSanitized = messageSanitized.replace("!sub ", "")
	areas = messageSanitized.split(',')
	
	#print(areas)
	
	notFound = []
	alreadySubbed = []
	added = []
	curUser = None
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None:
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [])
		symphonyUsers.append(curUser)
	
	# ensure all inputs are actually neighborhoods
	for area in areas:
		area = area.strip()
		area = area.lower()
		if area in geoDataDict:
			if area in added or area in curUser.subscriptions:
				alreadySubbed.append(area)
			else:
				added.append(area)
		else: notFound.append(area)
		
	for area in added:
		curUser.subscriptions.append(area)
	
	outputMessage = ""
	if len(added) > 0: outputMessage = outputMessage + "Added subscriptions for: " + ", ".join(added).title() + "\n"
	if len(alreadySubbed) > 0: outputMessage = outputMessage + "Already subscribed to: " + ", ".join(alreadySubbed).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a neighborhood for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()
	return outputMessage

def unsubscribeLogic(ctx):	
	message = ctx.message
	messageSanitized = message.content.replace("!unsubscribe ", "")
	messageSanitized = messageSanitized.replace("!unsub ", "")
	areas = messageSanitized.split(',')
	
	#print(areas)
	
	notFound = []
	notSubbed = []
	unsubbed = []
	curUser = None
	
	outputMessage = ""
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None: 
		outputMessage = "You currently have no subscriptions."
	else:
		for area in areas:
			area = area.strip()
			if area.lower() in geoDataDict:
				if area in curUser.subscriptions:
					curUser.subscriptions.remove(area)
					unsubbed.append(area)	
				else:
					notSubbed.append(area)
			else: 
				notFound.append(area)

	if len(unsubbed) > 0: outputMessage = outputMessage + "Removed subscriptions for: " + ", ".join(unsubbed).title() + "\n"
	if len(notSubbed) > 0: outputMessage = outputMessage + "Not subscribed to: " + ", ".join(notSubbed).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a neighborhood for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()
	return outputMessage

def getSubscriptions(ctx):
	outputMessage = "No subscriptions"
	for user in symphonyUsers:
		if user.name == ctx.message.author.name:
			outputMessage = ", ".join(user.subscriptions).title()
	return outputMessage
	
@symphony.event
async def on_ready():
	global server
	print("Client logged in")
	server = symphony.get_server('288536871330512896')
	
'''
@symphony.command()
async def pokemon(number):
	await symphony.say(pokemonList[number]["name"])

@symphony.command()
async def move(number):
	await symphony.say(moveList[number]["name"])
'''
	

@symphony.command(pass_context = True, description = "Ex: !subscribe Northgate, River Trail")
async def subscribe(ctx):
	'''Subscribe for neighborhood alerts'''
	outputMessage = subscribeLogic(ctx)
	await symphony.say(outputMessage)

@symphony.command(pass_context = True, description = "Ex: !sub Northgate, River Trail")
async def sub(ctx):
	'''Subscribe alt command'''
	outputMessage = subscribeLogic(ctx)
	await symphony.say(outputMessage)	

@symphony.command(pass_context = True, description = "Ex: !Unsubscribe Northgate, Lake City")
async def unsubscribe(ctx):
	'''Unsubscribe from particular neighborhood alerts'''
	outputMessage = unsubscribeLogic(ctx)
	await symphony.say(outputMessage)	
	
@symphony.command(pass_context = True, description = "Ex: !Unsub Northgate, Lake City")
async def unsub(ctx):
	'''Unsubscribe alt command'''
	outputMessage = unsubscribeLogic(ctx)
	await symphony.say(outputMessage)	

@symphony.command(pass_context = True)
async def subscriptions(ctx):
	'''List your subscriped neighborhoods'''
	outputMessage = getSubscriptions(ctx)
	await symphony.say(outputMessage)	

@symphony.command(pass_context = True)
async def subs(ctx):
	'''Subscriptions alt command'''
	outputMessage = getSubscriptions(ctx)
	await symphony.say(outputMessage)
	
@symphony.command()
async def isArea(*, message: str):
	'''Internal command, checks if a string is a valid neighborhood name'''
	await symphony.say(isNeighborhoodInternal(message))

@symphony.command()
async def areaList(letter: str):
	'''Internal command, lists neighborhoods starting with a specific character'''
	outputMessage = ""
	areas = []
	
	for area in geoDataDict:
		if area[0] == letter.lower(): 
			areas.append(area)
	
	if len(areas) == 0: outputMessage = "No neighborhoods found that start with " + letter + "."
	else:
		areas.sort()
		outputMessage = "Neighborhoods that start with " + letter + ": "
		outputMessage = outputMessage + ", ".join(areas).title()
		
	await symphony.say(outputMessage)

@symphony.command()
async def users():
	'''Internal command, shows how many current users there are and lists their names'''
	msg = "Current users: " + str(len(symphonyUsers))
	
	for user in symphonyUsers:
		msg = msg + "\n" + user.name
	
	await symphony.say(msg)

@symphony.command(description = "Ex: !userSubs Trapsin")
async def userSubs(userName: str):
	'''Internal command, shows a user's subs'''
	for user in symphonyUsers:
		if user.name == userName:
			msg = " ".join(user.subscriptions)
	await symphony.say(msg)

@symphony.group(pass_context=True)
async def filter(ctx):
    if ctx.invoked_subcommand is None:
        await symphony.say('Invalid filter command passed...')

@filter.command()
async def add():
    await symphony.say("Adding pokemon")	

@filter.command()
async def remove():
    await symphony.say("Removing pokemon")

@filter.command()
async def list():
    await symphony.say("Listing pokemon")		
	
@symphony.event
async def on_message(message):
	# we do not want the bot to reply to itself
	if message.author == symphony.user:
		return
	
	if message.channel.id == input.id:
		s = readInput(message.content)
		#msg = message.channel
		await symphony.send_message(all, embed = s.message)
		
		# special cases
		# 100 iv
		if (s.ivTotal == 45): 
			await symphony.send_message(perfectIV, embed = s.message)
		# dratini fam	
		if (s.pokemon_id == 147 or s.pokemon_id == 148 or s.pokemon_id == 149):
			await symphony.send_message(dratini, embed = s.message)
		# larvitar fam
		if (s.pokemon_id == 246 or s.pokemon_id == 247 or s.pokemon_id == 248):
			await symphony.send_message(larvitar, embed = s.message)
		# rares: snorlax, lapras, blissey fam
		if (s.pokemon_id == 143 or s.pokemon_id == 131 or s.pokemon_id == 113 or s.pokemon_id == 242):
			await symphony.send_message(rares, embed = s.message)
		
		#print("Finding subbed users for " + s.locationName)
		subs = findSubcribedUsers(s.locationName)
		#print("Found " + str(len(subs)) + " subbed users")
		#if len(subs) > 0:
			#for sub in subs:
				#print(sub.name)

		for sub in subs:
			sendToUser = server.get_member(sub.id)
			await symphony.send_message(sendToUser, embed = s.message)
			
	else: 
		await symphony.process_commands(message)
		

pokemonList = loadPokemon()
moveList = loadMoves()	
loadGeoData()
importUsers()
symphony.run("Mjg4NTYwMTI5MTAyNzA4NzM3.C5_mKg.G3lfXpkqnvr8ocJxnfKJ7YPO3pE")
atexit.register(exit_handler)