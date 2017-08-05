import discord
from discord.ext.commands import Bot
import json
import sys
import datetime
from shapely.geometry import Point, MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.ops import cascaded_union
import atexit
import threading

symphony = Bot(command_prefix = "!")
server = "unnasigned"
pokemonList = {}
moveList = {}
geoDataDict = {}
symphonyUsers = []
exportedRecently = False
logFile = "log.txt"
messagesReadPerMinute = 0
feedsSentPerMinute = 0
directMessagesSentPerMinute = 0
inputPerMinute = 0
commandsPerMinute = 0

input = discord.Object(id = '288563630645968896')	# where the input feed is being posted
support = discord.Object(id = '302183093140324352')	# the only channel commands will be read from

# test server channels
troubleshooting = discord.Object(id = '300686505066889216')
all = discord.Object(id = '297541247378391042')

# feeds
rares = discord.Object(id = '294107396442292224') 	# snorlax-chancey-lapras-porygon
perfectIV = discord.Object(id = '292195941279072276')
dratini = discord.Object(id = '292196045717241857')
larvitar = discord.Object(id = '292196235673337856')
lapras = discord.Object(id = '292195992881594371')
snorlax = discord.Object(id = '292196012511068160')
chansey = discord.Object(id = '292196119432134657')
grimer = discord.Object(id = '295375572639416321')
hitmonchanLeeTop = discord.Object(id = '295400320484245504')
mareep = discord.Object(id = '292196086456516610')
unown = discord.Object(id = '292195967191613440')
starters = discord.Object(id = '310199103231623168')	# gen 1 & 2
hugeMons = discord.Object(id = '313086330609467393')		# CP >= 2500

class Spawn:
	def __init__(self):
		self.pokemon_id = ""
		self.move_1 = ""
		self.move_2 = ""
		self.gender = ""
		self.form = ""
		
		self.cp = 0
		self.trainerLevel = 0
		
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
		try:
			self.ivTotal = self.individual_attack + self.individual_defense + self.individual_stamina
			p = self.ivTotal / 45
			p = p * 100
			self.percent = round(p, 1)
		except BaseException as e:
			self.ivTotal = -1
			log("IV Error" + str(e))
	
	def getNames(self):
		self.pokemonName = pokemonList[str(self.pokemon_id)]["name"]
		try:
			self.move1Name = moveList[str(self.move_1)]["name"]
		except:
			self.move1Name = "Move not found"
			log("Error retreiving move name")
		try:
			self.move2Name = moveList[str(self.move_2)]["name"]
		except:
			self.move2Name = "Move not found"
		
		if self.gender == 1: self.gender = '\u2642'
		else: self.gender = '\u2640'
		
		et = (datetime.datetime.now() + datetime.timedelta(seconds = self.seconds_until_despawn)).time()
		self.expireTime = et.strftime('%H:%M:%S')
		
		hours, remainder = divmod(self.seconds_until_despawn, 3600)
		minutes, seconds = divmod(remainder, 60)
		self.remainingTime = '%sm %ss' % (minutes, seconds)
		
		self.link = "http://maps.google.com/maps?q="+ str(self.latitude) + "," + str(self.longitude)
		
		if (self.longitude == -1 or self.latitude == -1): 
			self.locationName = "test hood"
			return
		self.locationName = findNeighborhood([self.longitude, self.latitude])
		
	def buildMessage(self):	
		title = self.pokemonName+" "+self.gender+" | CP: "+str(self.cp)
		description = "**IV:** "+str(self.percent)+"% ("+str(self.individual_attack)+"/"+str(self.individual_defense)+"/"+str(self.individual_stamina)+")\n**MoveSet:** "+str(self.move1Name)+"/"+str(self.move2Name)+"\n**Location:** "+self.locationName.title()+"\n**Until:** "+self.expireTime+" ("+self.remainingTime+")"
		
		if self.percent > 99: ivColor = discord.Color.orange()
		elif self.percent > 90: ivColor = discord.Color.purple()
		elif self.percent > 80: ivColor = discord.Color.blue()
		elif self.percent > 50: ivColor = discord.Color.green()
		elif self.percent > 25: ivColor = discord.Color(0xffffff)
		else: ivColor = discord.Color.light_grey()
		
		self.message = discord.Embed(title = title, color = ivColor, url = self.link, description = description)
		self.message.set_thumbnail(url="https://raw.githubusercontent.com/kvangent/PokeAlarm/master/icons/" + str(self.pokemon_id) +  ".png")

class SymphonyUser:
	def __init__(self, name_, id_, discriminator_, subscriptions_, filters_, default_, cpFilters_ = {}, cpDefault_ = 0):
		self.name = name_
		self.id = id_
		self.discriminator = discriminator_
		self.subscriptions = subscriptions_
		self.filters = filters_
		self.default = default_
		self.cpFilters = cpFilters_
		self.cpDefault = cpDefault_

def exit_handler():
	exportUsers()
	log("Symphony Closing")

def log(message, special = "none"):
	
	if special == "bottleneck":
		msg = message + " at " + datetime.datetime.now().strftime('%m/%d/%y %I:%M:%S:%f %p')
		f = open("bottleNeck.txt", 'a')
		print(msg, file = f)
		f.close()
		return
	
	if special == "time":
		msg = message + " at " + datetime.datetime.now().strftime('%m/%d/%y %I:%M:%S:%f %p')
		f = open("responseTime.txt", 'a')
		print(msg, file = f)
		f.close()
		return
		
	msg = message + " at " + datetime.datetime.now().strftime('%m/%d/%y %I:%M:%S %p')
	print(msg)
		
	f = open(logFile, 'a')
	print(msg, file = f)
	f.close()
	
	if special == "apm":
		f = open("apm.txt", 'a')
		print(msg, file = f)
		f.close()
		
	if special == "runLog":
		f = open("runLog.txt", 'a')
		print(msg, file = f)
		f.close()
	
def exportUsers():
	global exportedRecently
	
	if exportedRecently == False:
		log("Exporting users")

		userData = json.dumps([symphonyUser.__dict__ for symphonyUser in symphonyUsers])

		f = open('users.json', 'w')
		f.write(userData)
		f.close()
		
		exportedRecently = True
		
def importUsers():
	global symphonyUsers
	
	log("Importing Users")
	
	with open("users.json", "r", encoding='utf-8') as data_file:   
		userData = json.load(data_file)
	
	for symphonyUser in userData: 
		try:
			su = SymphonyUser(symphonyUser["name"], symphonyUser["id"], symphonyUser["discriminator"], symphonyUser["subscriptions"], symphonyUser["filters"], symphonyUser["default"], symphonyUser["cpFilters"], symphonyUser["cpDefault"])
		except:
			su = SymphonyUser(symphonyUser["name"], symphonyUser["id"], symphonyUser["discriminator"], symphonyUser["subscriptions"], symphonyUser["filters"], symphonyUser["default"], {}, 0)
		symphonyUsers.append(su)
		
	log("Users Imported")
	
def findNeighborhood(pointCoords):
	point = Point(pointCoords)
	for label, shape in geoDataDict.items():
		if (shape.contains(point)):
			return label
	log("Neighborhood not found")
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
	#northGeoJSON = loadDataFromJson("north.geoJSON")
	#southGeoJSON = loadDataFromJson("south.geoJSON")
	#regions = [northGeoJSON, southGeoJSON]
	
	SPMgeo = loadDataFromJson("GeoFence.geoJSON")
	regions = [SPMgeo]
	
	
	for region in regions:
		for area in region["features"]:
			areaLabel = area["properties"]["label"]
			shape = createShape(area)
			geoDataDict[areaLabel.lower()] = shape

# preps geoJSON coords to create shapely multipolygon
# http://gis.stackexchange.com/questions/70591/creating-shapely-multipolygons-from-shapefile-multipolygons
def PrepCoordsForShapely(rawcoords):
    preppedcoords = []
    # according to the geojson specs, a multipolygon is a list of linear rings, so we loop each
    for eachpolygon in rawcoords:
        # the first linear ring is the coordinates of the polygon, and shapely needs it to be a tuple
        tupleofcoords = tuple(eachpolygon[0])
        # the remaining linear rings, if any, are the coordinates of inner holes, and shapely needs these to be nested in a list
        if len(eachpolygon) > 1:
            listofholes = list(eachpolygon[1:])
        else:
            listofholes = []
        # shapely defines each polygon in a multipolygon with the polygoon coordinates and the list of holes nested inside a tuple
        eachpreppedpolygon = (tupleofcoords, listofholes)
        # so append each prepped polygon to the final multipolygon list
        preppedcoords.append(eachpreppedpolygon)
    # finally, the prepped coordinates need to be nested inside a list in order to be used as a star-argument for the MultiPolygon constructor.
    return [preppedcoords]
	
def readInput(spawnData):
	log("Spawn started\t\t\t\t\t\t\t\t", "bottleneck")
	s = Spawn()
	log("Loading JSON\t\t\t\t\t\t\t\t", "bottleneck")
	sd = json.loads(spawnData)
	log("JSON Loaded, parsing JSON\t\t\t\t\t", "bottleneck")
	s.pokemon_id = sd.get("pokemon_id")
	s.move_1 = sd.get("move_1")
	s.move_2 = sd.get("move_2")
	s.cp = sd.get("cp")
	s.trainerLevel = sd.get("player_level")
	s.form = sd.get("form")
	s.individual_attack = sd.get("individual_attack")
	s.individual_defense = sd.get("individual_defense")
	s.individual_stamina = sd.get("individual_stamina")
	s.longitude = sd.get("longitude")
	s.latitude = sd.get("latitude")
	s.seconds_until_despawn = sd.get("seconds_until_despawn")
	log("JSON Parsed, calling getNames\t\t\t\t", "bottleneck")
	if s.seconds_until_despawn == None: s.seconds_until_despawn = int(sd.get("disappear_time") / 1000) 	# disappear_time is in ms, / 1000 to convert to seconds
	s.getNames()
	log("getNames finished, calling calcPercent\t\t", "bottleneck")
	s.calculatePercent()
	log("calcPercent finished, calling buildMessage\t", "bottleneck")
	s.buildMessage()
	log("BuildMessage finished\t\t\t\t\t\t", "bottleneck")
	log("Spawn finished\t\t\t\t\t\t", "bottleneck")
	return s

def findSubcribedUsers(neighborhood):
	subscribedUsers = []
	for user in symphonyUsers:
		if neighborhood in user.subscriptions: subscribedUsers.append(user)
	return subscribedUsers

def ivFilterOutSubs(subList, pokemonName, percent):
	subsToDM = []
	
	for subbedUser in subList:
		# check if subbedUser has a filter for the pokemon
		if pokemonName in subbedUser.filters:
			# check if the filter is lower than pokemon IV
			if (subbedUser.filters[pokemonName] <= percent):
				# add to DM List
				subsToDM.append(subbedUser)		
		else:	# if no filter, check the default
			if subbedUser.default <= percent:
				subsToDM.append(subbedUser)
			
	return subsToDM
	
def cpFilterOutSubs(subList, pokemonName, cp):
	subsToDM = []
	
	for subbedUser in subList:
		# check if subbedUser has a filter for the pokemon
		if pokemonName in subbedUser.cpFilters:
			# check if the filter is lower than pokemon IV
			if (subbedUser.cpFilters[pokemonName] <= cp):
				# add to DM List
				subsToDM.append(subbedUser)		
		else:	# if no filter, check the default
			if subbedUser.cpDefault <= cp:
				subsToDM.append(subbedUser)
			
	return subsToDM
	
def isNeighborhoodInternal(neighborhood):
	neighborhood = neighborhood.strip()
	return neighborhood.lower() in geoDataDict

def subscribeLogic(ctx):
	message = ctx.message
	if (message.content.strip() == "!sub" or message.content.strip() == "!subscribe"): 
		return  "What neighborhood would you like to subscribe to? ie: `!sub capitol hill`"
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
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [], {}, 0, {}, 0)
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
	
	if (message.content.strip() == "!unsub" or message.content.strip() == "!unsubscribe"): return  "What neighborhood would you like me to remove from your `!sub list`"
	
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
			area = area.lower()
			if area in geoDataDict:
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
	outputMessage = "You're not subscribed to any locations."
	for user in symphonyUsers:
		if user.id == ctx.message.author.id:
			if len(user.subscriptions) > 0:
				outputMessage = ", ".join(user.subscriptions).title()
			break
	return outputMessage

def greeting(ctx):
	return ctx.message.author.mention + ", "

def exportTimer():
	global exportedRecently
	threading.Timer(60.0, exportTimer).start()
	exportedRecently = False
		
def actionsPerMinuteTimer():
	global messagesReadPerMinute
	global inputPerMinute
	global commandsPerMinute
	global directMessagesSentPerMinute
	global feedsSentPerMinute
	
	threading.Timer(300.0, actionsPerMinuteTimer).start()
	log("MRPM: " + str(messagesReadPerMinute / 5) + "\tCPM: " + str(commandsPerMinute / 5) + "\tIPM: " + str(inputPerMinute / 5) + "\tFPM: " + str(feedsSentPerMinute / 5) + "\tDMPM: " + str(directMessagesSentPerMinute / 5), "apm")
	
	messagesReadPerMinute = 0
	inputPerMinute = 0
	commandsPerMinute = 0
	directMessagesSentPerMinute = 0
	feedsSentPerMinute = 0
	

def splitMessageInto2kChunks(msg):
	return (msg[i : i + 2000] for i in range(0, len(msg), 2000))
	
@symphony.event
async def on_ready():
	global server		
	log("Symphony started", "runLog")
	server = symphony.get_server('292040545134706699')	#SPM+
	
@symphony.command(hidden = True)
async def pokemon(number):
	await symphony.say(pokemonList[number]["name"])

@symphony.command(hidden = True)
async def show(*, loc: str):
	userList = []
	
	for user in symphonyUsers:
		if (loc in user.subscriptions):
			userList.append(user)
	
	msg = str(len(userList)) + " users:"
	
	for u in userList:
		msg += "\n" + u.name
	
	await symphony.say(msg)
		
@symphony.command(hidden = True, enabled = True)
async def test():	

	global commandsPerMinute
	commandsPerMinute += 1
	
	outputMessage = ""
	default = 0
	for user in symphonyUsers:
		if user.id == "298875104010436608":
			default = user.default
			for k, v in user.filters.items():
				outputMessage = outputMessage + k + ":" + str(v) + ", "
			break
	if len(outputMessage) == 0: outputMessage = "No filters found."
	
	outputMessage = outputMessage.replace("101", "Blocked")
	outputMessage = outputMessage.strip(', ')
	outputMessage = "Your default filter IV is: " + str(default) + "\nYour filter list is: " + outputMessage
	
	if len(outputMessage) <= 1960:
		outputMessage = "HedakomKongeda, " + outputMessage
		print(outputMessage)
		await symphony.say(outputMessage)
	else:
		over2kMsg = "HedakomKongeda, " + "Your filter list is over 2000 characters, sending the results as a direct message."
		await symphony.say(over2kMsg)
		for under2kMsg in splitMessageInto2kChunks(outputMessage):
			await symphony.say(under2kMsg)	
	
	'''
	location = "firdale" 
	pokemonName = "Togetic"
	percent = 49
	
	
	subsToHood = findSubcribedUsers(location)
	subs = checkSubscribedUserFilters(subsToHood, pokemonName, percent)
	try:
		subs2 = filterOutSubs(subsToHood, pokemonName, percent)
	except BaseException as e:
		subs2 = []
		log("subs2 DED")
		log(e)
	
	try: print("Filter check " + location + " for: " + pokemonName + ":" + str(percent) + "\n" + str(len(subsToHood)) + "----" + str(len(subs)) + "----" + str(len(subs2)))
	except: print("Can't msg")
	
	
	for s1 in subsToHood:
		try: 
			try: msg = str(s1.filters[pokemonName]) + " - " + str(s1.default)
			except: msg = "No filter" + " - " + str(s1.default)
			log("\t" + s1.name + ": " + msg)
		except: 
			try: msg = str(s1.filters[pokemonName]) + " - " + str(s1.default)
			except: msg = "No filter" + " - " + str(s1.default)
			log("\t" + s1.id + ": " + msg)
	print("----------------------------------")
	for s1 in subs:
		try: 
			try: msg = str(s1.filters[pokemonName]) + " - " + str(s1.default)
			except: msg = "No filter" + " - " + str(s1.default)
			log("\t" + s1.name + ": " + msg)
		except: 
			try: msg = str(s1.filters[pokemonName]) + " - " + str(s1.default)
			except: msg = "No filter" + " - " + str(s1.default)
			log("\t" + s1.id + ": " + msg)
	print("----------------------------------")
	for s2 in subs2:
		try: 
			try: msg = str(s2.filters[pokemonName]) + " - " + str(s2.default)
			except: msg = "No filter" + " - " + str(s2.default)
			log("\t" + s2.name + ": " + msg)
		except: 
			try: msg = str(s2.filters[pokemonName]) + " - " + str(s2.default)
			except: msg = "No filter" + " - " + str(s2.default)
			log("\t" + s2.id + ": " + msg)
	
	'''
	await symphony.say('✿')

@symphony.command(aliases = ["neighborhoods"])
async def hoods():
	'''Provides the link for the Neighborhood map'''
	# SPM bot handles the command, just adding so it shows up in the help list
	#await symphony.say("For a list of Neighborhoods: http://doctypestudios.com/SPM/Neighborhoods.html")
	return
	
@symphony.command(enabled = False, hidden = True)
async def move(number):
	await symphony.say(moveList[number]["name"])

@symphony.group(pass_context = True, description = "Ex: !sub Northgate, River Trail", aliases = ["subscribe"])
async def sub(ctx):
	'''Subscribe for neighborhood alerts'''
	global commandsPerMinute
	commandsPerMinute += 1
	if ctx.invoked_subcommand is None:
		outputMessage = greeting(ctx) + subscribeLogic(ctx)
		await symphony.say(outputMessage)		

@sub.command(pass_context = True, description = "Ex: !filter add Squirtle:90, Bulbasaur:95, Charmander:100")
async def list(ctx):
	'''List your subscriped neighborhoods'''
	global commandsPerMinute
	commandsPerMinute += 1
	outputMessage = "Your subscriptions are: " + getSubscriptions(ctx)
	
	if len(outputMessage) <= 1960:
		outputMessage = greeting(ctx) + outputMessage
		await symphony.say(outputMessage)
	else:
		over2kMsg = greeting(ctx) + "Your subs list is over 2000 characters, sending the results as a direct message."
		await symphony.say(over2kMsg)
		for under2kMsg in splitMessageInto2kChunks(outputMessage):
			await symphony.send_message(ctx.message.author, under2kMsg)

@symphony.command(pass_context = True, description = "Ex: !Unsub Northgate, Lake City", aliases = ["unsubscribe"])
async def unsub(ctx):
	'''Unsubscribe from particular neighborhood alerts'''
	global commandsPerMinute
	commandsPerMinute += 1
	outputMessage = greeting(ctx) + unsubscribeLogic(ctx)
	await symphony.say(outputMessage)	

@symphony.command(pass_context = True, aliases = ["subscriptions"])
async def subs(ctx):
	'''List your subscriped neighborhoods'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	outputMessage = "Your subscriptions are: " + getSubscriptions(ctx)
	
	if len(outputMessage) <= 1960:
		outputMessage = greeting(ctx) + outputMessage
		await symphony.say(outputMessage)
	else:
		over2kMsg = greeting(ctx) + "Your subs list is over 2000 characters, sending the results as a direct message."
		await symphony.say(over2kMsg)
		for under2kMsg in splitMessageInto2kChunks(outputMessage):
			await symphony.send_message(ctx.message.author, under2kMsg)
	
@symphony.command(pass_context = True, description = "Ex: !isLoc Ballard", aliases = ["isloc"])
async def isLoc(ctx):
	'''Checks if a string is a valid neighborhood name'''
	global commandsPerMinute
	commandsPerMinute += 1
	if (ctx.message.content.lower() == "!isloc"):
		outputMessage = greeting(ctx) + "Provide a neighborhood name to see if it exists, ie: `!isLoc Ballard`"
		await symphony.say(outputMessage)
		return
	
	locationName = ctx.message.content.replace("!isLoc ", "")
	locationName = locationName.replace("!isloc ", "")
	if (isNeighborhoodInternal(locationName) == True):
		exists  = "does"
	else: exists = "doesn't"
	
	outputMessage  = "that location " + exists + " exist."
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)

@symphony.command(pass_context = True, description = "Ex: !areaList B", aliases = ["arealist"])
async def areaList(ctx):
	'''Find neighborhoods starting with a specific letter'''
	global commandsPerMinute
	commandsPerMinute += 1
	input = ctx.message.content.strip()
	
	if (input.lower() == "!arealist" or len(input) > 11): 
		await symphony.say(greeting(ctx) + "To use this command provide a single letter, ie. `!areaList B`")
		return
	
	outputMessage = ""
	areas = []
	
	
	letter = input.replace("!areaList ", "")
	letter = letter.replace("!arealist ", "")
	letter = letter.lower()
	for area in geoDataDict:
		if area[0] == letter: 
			areas.append(area)
	
	if len(areas) == 0: outputMessage = "No neighborhoods found that start with **" + letter + "**."
	else:
		areas.sort()
		outputMessage = "Neighborhoods that start with **" + letter + "**: "
		outputMessage = outputMessage + ", ".join(areas).title()
		
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)

@symphony.command(hidden = True)
async def users():
	'''Internal command, shows how many current users there are and lists their names'''
	global commandsPerMinute
	commandsPerMinute += 1
	msg = "Current users: " + str(len(symphonyUsers))
	
	for user in symphonyUsers:
		msg = msg + ", " + user.name
	
	msg.strip(',')
	await symphony.say(msg)

@symphony.command(description = "Ex: !userSubs Trapsin", hidden = True)
async def userSubs(userName: str):
	'''Internal command, shows a user's subs'''
	global commandsPerMinute
	commandsPerMinute += 1
	if (len(userName) == 0):
		await symphony.say(self.description)
		return
	
	msg = "No subs found."
	
	
	for user in symphonyUsers:
		if user.name == userName:
			if len(user.subscriptions) > 0:
				msg = " ".join(user.subscriptions)
			break
	
	if len(msg) <= 1960:
		await symphony.say(msg)
	else:
		for under2kMsg in splitMessageInto2kChunks(msg):
			await symphony.say(under2kMsg)

@symphony.command(description = "Ex: !userFilters Trapsin", hidden = True)
async def userFilters(userName: str):
	'''Internal command, shows a user's filters'''
	global commandsPerMinute
	commandsPerMinute += 1
	msg = ""
	for user in symphonyUsers:
		if user.name == userName:
			for k, v in user.filters.items():
				msg = msg + k + ":" + str(v) + " "
			break
	if len(msg) == 0: msg = "No filters found."
	await symphony.say(msg)
	
@symphony.group(pass_context = True)
async def filter(ctx):
	'''Manage custom filters for your subscriptions'''
	global commandsPerMinute
	commandsPerMinute += 1
	if ctx.invoked_subcommand is None:
		outputMessage = greeting(ctx) + '''this command has multiple uses:
		`!filter add POKEMON:IV` » Add a Pokémon to your `!filter list`
		`!filter remove POKEMON` »  Remove a Pokémon from your `!filter list`
		`!filter default IV` »  Set your default minimum IV filter for all Pokémon
		`!filter block POKEMON` » Block a Pokémon from being messaged to you
		`!filter list` » View your currently active filter list.'''
		await symphony.say(outputMessage)	

@filter.command(pass_context = True, description = "Ex: !filter add Squirtle:90, Bulbasaur:95, Charmander:100")
async def add(ctx):
	'''Add a filter'''
	global commandsPerMinute
	commandsPerMinute += 1
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip() == "!filter add"):
		outputMessage = greeting(ctx) + "What Pokémon would you like me to add to your `!filter list`"
		await symphony.say(outputMessage)
		return
	
	if (':' in message.content) == False:
		outputMessage = greeting(ctx) + "To add to your `!filter list` use the format `!filter add POKEMON:IV`"
	
	messageSanitized = message.content.replace("!filter add ", "")
	filters = messageSanitized.split(',')
	
	notFound = []
	changed = []
	added = []
	curUser = None
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None:
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [], {}, 0, {}, 0)
		symphonyUsers.append(curUser)
	
	# ensure all inputs are actually pokemon
	for filter in filters:
		try:
			pokemon, ivValue = filter.split(":")
			try:
				ivValue = int(ivValue)
			except:
				await symphony.say(greeting(ctx) + "IV Value must be a number, ie: !filter add Squirtle:95")
				return
		except:
			pokemon = filter
		pokemon = pokemon.strip()
		pokemon = pokemon.title()
		
		found = False
		for pokemonNumber, pokemonData in pokemonList.items():
			if pokemonData["name"] == pokemon:
				if pokemon in curUser.filters:
					changed.append(filter)
				else:
					added.append(filter)
				
				found = True
				curUser.filters[pokemon] = ivValue
				break
				
		if found == False: notFound.append(pokemon)
	
	outputMessage = ""
	if len(added) > 0: outputMessage = outputMessage + "Added filters for: " + ", ".join(added).title() + "\n"
	if len(changed) > 0: outputMessage = outputMessage + "Filters updated for: " + ", ".join(changed).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a pokemon for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)	

@filter.command(pass_context = True, description = "Ex: !filter remove Squirtle, Bulbasaur")
async def remove(ctx):
	'''Remove a filter'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip() == "!filter remove"):
		outputMessage = greeting(ctx) + "What Pokémon would you like me to remove from your `!filter list`"
		await symphony.say(outputMessage)
		return
		
	messageSanitized = message.content.replace("!filter remove ", "")
	filters = messageSanitized.split(',')
	
	#print(filters)
	
	notFound = []
	noFilter = []
	removed = []
	curUser = None
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None:
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [], {}, 0, {}, 0)
		symphonyUsers.append(curUser)
	
	# ensure all inputs are actually pokemon
	for pokemon in filters:
		pokemon = pokemon.strip()
		pokemon = pokemon.title()

		found = False
		for pokemonNumber, pokemonData in pokemonList.items():
			if pokemonData["name"] == pokemon:
				if pokemon in curUser.filters:
					removed.append(pokemon)
					curUser.filters.pop(pokemon)
				else:
					noFilter.append(pokemon)
				
				found = True
				break
		
		if found == False: notFound.append(pokemon)
	
	outputMessage = ""
	if len(removed) > 0: outputMessage = outputMessage + "Removed filters for: " + ", ".join(removed).title() + "\n"
	if len(noFilter) > 0: outputMessage = outputMessage + "No filter exists for: " + ", ".join(noFilter).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a pokemon for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()
	
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)	
	
@filter.command(pass_context = True, description = "Ex: !filter block Wartortle, Exeggcute")
async def block(ctx):
	'''Block a Pokémon from showing in your subscriptions'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip() == "!block"): 
		outputMessage = greeting(ctx) + "What Pokémon would you like me to block from your `!filter list`"
		await symphony.say(outputMessage)
		return
	
	messageSanitized = message.content.replace("!filter block ", "")
	filters = messageSanitized.split(',')
	
	#print(filters)
	
	notFound = []
	changed = []
	added = []
	curUser = None
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None:
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [], {}, 0, {}, 0)
		symphonyUsers.append(curUser)
	
	# ensure all inputs are actually pokemon
	for pokemon in filters:
		pokemon = pokemon.strip()
		pokemon = pokemon.title()
		
		found = False
		for pokemonNumber, pokemonData in pokemonList.items():
			if pokemonData["name"] == pokemon:
				if pokemon in curUser.filters:
					changed.append(pokemon)
				else:
					added.append(pokemon)
					
				found = True
				curUser.filters[pokemon] = 101
				break
		if found == False: notFound.append(pokemon)
	
	outputMessage = ""
	if len(added) > 0: outputMessage = outputMessage + "Added blocks for : " + ", ".join(added).title() + "\n"
	if len(changed) > 0: outputMessage = outputMessage + "Filters updated for: " + ", ".join(changed).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a pokemon for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()

	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)	

@filter.command(pass_context = True)
async def default(ctx):
	'''Sets your default minimum IV filter for all pokemon'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip() == "!filter default"): 
		outputMessage = greeting(ctx) + "What minimum IV would you like to set as your default?"
		await symphony.say(outputMessage)
		return
	
	messageSanitized = message.content.replace("!filter default ", "")
	
	try:
		default = int(messageSanitized)
	except:
		outputMessage = greeting(ctx) + "The command should be in the format `!filter default IV`"
		await symphony.say(outputMessage)
		return
	
	for user in symphonyUsers:
		if user.id == message.author.id:
			user.default = default
			break
	
	exportUsers()
	
	outputMessage = greeting(ctx) + "Your default filter has been set to " + str(default)
	await symphony.say(outputMessage)

@filter.command(pass_context = True)
async def clear(ctx):
	'''Clears your filter list'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	outputMessage = "To clear your `!filter list` enter the command `!filter clear yes`. Make sure you want to do this as your list will be cleared and can't be recovered. It is recommended to run the `!filter list` command before you do this so you have it as a reference of your old list."
	
	if (message.content == "!filter clear yes" or message.content == "!filter clear Yes"):
		for user in symphonyUsers:
			if user.id == message.author.id:
				user.filters = {}
				outputMessage = "Your `!filter list` has been cleared."
				break
	
	exportUsers()
	
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)		
	
@filter.command(pass_context = True)
async def list(ctx):
	'''List your custom filters'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	outputMessage = ""
	default = 0
	for user in symphonyUsers:
		if user.id == ctx.message.author.id:
			default = user.default
			for k, v in user.filters.items():
				outputMessage = outputMessage + k + ":" + str(v) + ", "
			break
	if len(outputMessage) == 0: outputMessage = "No filters found."
	
	outputMessage = outputMessage.replace("101", "Blocked")
	outputMessage = outputMessage.strip(', ')
	outputMessage = "Your default filter IV is: " + str(default) + "\nYour filter list is: " + outputMessage
	
	if len(outputMessage) <= 1960:
		outputMessage = greeting(ctx) + outputMessage
		await symphony.say(outputMessage)
	else:
		over2kMsg = greeting(ctx) + "Your filter list is over 2000 characters, sending the results as a direct message."
		await symphony.say(over2kMsg)
		for under2kMsg in splitMessageInto2kChunks(outputMessage):
			await symphony.send_message(ctx.message.author, under2kMsg)	

	
@symphony.group(pass_context = True, aliases = ["cp"])
async def cpfilter(ctx):
	'''Manage custom CP filters for your subscriptions'''
	global commandsPerMinute
	commandsPerMinute += 1
	if ctx.invoked_subcommand is None:
		outputMessage = greeting(ctx) + '''this command has multiple uses:
		`!cpfilter add POKEMON:CP` » Add a Pokémon to your `!filter cp list`
		`!cpfilter remove POKEMON` »  Remove a Pokémon from your `!filter cp list`
		`!cpfilter default CP` »  Set your default minimum CP filter for all Pokémon
		`!cpfilter list` » View your currently active CP filter list.'''
		await symphony.say(outputMessage)		
	
@cpfilter.command(pass_context = True, description = "Ex: !cpfilter add Snorlax:2000, Bulbasaur:500, Charizard:1300")
async def add(ctx):
	'''Add a CP filter'''
	global commandsPerMinute
	commandsPerMinute += 1
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip().lower() == "!cpfilter add") or (message.content.strip().lower() == "!cp add"):
		outputMessage = greeting(ctx) + "What Pokémon would you like me to add to your `!cpfilter list`"
		await symphony.say(outputMessage)
		return
	
	if (':' in message.content) == False:
		outputMessage = greeting(ctx) + "To add to your `!cpfilter list` use the format `!cpfilter add POKEMON:CP`"
		await symphony.say(outputMessage)
		return
	
	messageSanitized = message.content.replace("!cpfilter add ", "")
	messageSanitized = messageSanitized.replace("!cp add ", "")
	filters = messageSanitized.split(',')
	
	notFound = []
	changed = []
	added = []
	curUser = None
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None:
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [], {}, 0, {}, 0)
		symphonyUsers.append(curUser)
	
	# ensure all inputs are actually pokemon
	for filter in filters:
		try:
			pokemon, cpValue = filter.split(":")
			try:
				cpValue = int(cpValue)
			except:
				await symphony.say(greeting(ctx) + "CP Value must be a number, ie: !cpfilter add Squirtle:400")
				return
		except:
			pokemon = filter
		pokemon = pokemon.strip()
		pokemon = pokemon.title()
		
		found = False
		for pokemonNumber, pokemonData in pokemonList.items():
			if pokemonData["name"] == pokemon:
				if pokemon in curUser.cpFilters:
					changed.append(filter)
				else:
					added.append(filter)
				
				found = True
				curUser.cpFilters[pokemon] = cpValue
				break
				
		if found == False: notFound.append(pokemon)
	
	outputMessage = ""
	if len(added) > 0: outputMessage = outputMessage + "Added CP filters for: " + ", ".join(added).title() + "\n"
	if len(changed) > 0: outputMessage = outputMessage + "CP filters updated for: " + ", ".join(changed).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a pokemon for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)	

@cpfilter.command(pass_context = True, description = "Ex: !cpfilter remove Squirtle, Bulbasaur")
async def remove(ctx):
	'''Remove a cp filter'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip().lower() == "!cpfilter remove") or (message.content.strip().lower() == "!cp remove"):
		outputMessage = greeting(ctx) + "What Pokémon would you like me to remove from your `!cpfilter list`"
		await symphony.say(outputMessage)
		return
		
	messageSanitized = message.content.replace("!cpfilter remove ", "")
	messageSanitized = messageSanitized.replace("!cp remove ", "")
	filters = messageSanitized.split(',')
	
	#print(filters)
	
	notFound = []
	noFilter = []
	removed = []
	curUser = None
	
	# assign curUser to existing or new user
	for u in symphonyUsers:
		if u.id == message.author.id:
			curUser = u
			break
	
	if curUser == None:
		curUser = SymphonyUser(message.author.name, message.author.id, message.author.discriminator, [], {}, 0, {}, 0)
		symphonyUsers.append(curUser)
	
	# ensure all inputs are actually pokemon
	for pokemon in filters:
		pokemon = pokemon.strip()
		pokemon = pokemon.title()

		found = False
		for pokemonNumber, pokemonData in pokemonList.items():
			if pokemonData["name"] == pokemon:
				if pokemon in curUser.cpFilters:
					removed.append(pokemon)
					curUser.cpFilters.pop(pokemon)
				else:
					noFilter.append(pokemon)
				
				found = True
				break
		
		if found == False: notFound.append(pokemon)
	
	outputMessage = ""
	if len(removed) > 0: outputMessage = outputMessage + "Removed CP filters for: " + ", ".join(removed).title() + "\n"
	if len(noFilter) > 0: outputMessage = outputMessage + "No CP filter exists for: " + ", ".join(noFilter).title() + "\n"
	if len(notFound) > 0: outputMessage = outputMessage + "Could not find a pokemon for: " + ", ".join(notFound).title() + "\n"
	
	exportUsers()
	
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)		

@cpfilter.command(pass_context = True)
async def clear(ctx):
	'''Clears your filter list'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	outputMessage = "To clear your `!cpfilter list` enter the command `!cpfilter clear yes`. Make sure you want to do this as your list will be cleared and can't be recovered. It is recommended to run the `!cpfilter list` command before you do this so you have it as a reference of your old list."
	
	if (message.content.lower() == "!cpfilter clear yes"):
		for user in symphonyUsers:
			if user.id == message.author.id:
				user.cpfilters = {}
				outputMessage = "Your `!cpfilter list` has been cleared."
				break
	
	exportUsers()
	
	outputMessage = greeting(ctx) + outputMessage
	await symphony.say(outputMessage)		

@cpfilter.command(pass_context = True)
async def default(ctx):
	'''Sets your default minimum CP filter for all pokemon'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	message = ctx.message
	
	# provide help if no parameters given
	if (message.content.strip() == "!cpfilter default") or (message.content.strip() == "!cp default"): 
		outputMessage = greeting(ctx) + "What minimum CP would you like to set as your default?"
		await symphony.say(outputMessage)
		return
	
	messageSanitized = message.content.replace("!cpfilter default ", "")
	messageSanitized = messageSanitized.replace("!cp default ", "")
	
	try:
		cpDefault = int(messageSanitized)
	except:
		outputMessage = greeting(ctx) + "The command should be in the format `!cpfilter default CP`"
		await symphony.say(outputMessage)
		return
	
	for user in symphonyUsers:
		if user.id == message.author.id:
			user.cpDefault = cpDefault
			break
	
	exportUsers()
	
	outputMessage = greeting(ctx) + "Your default CP filter has been set to " + str(cpDefault)
	await symphony.say(outputMessage)
	
@cpfilter.command(pass_context = True)
async def list(ctx):
	'''List your custom CP filters'''
	global commandsPerMinute
	commandsPerMinute += 1
	
	
	outputMessage = ""
	cpDefault = 0
	for user in symphonyUsers:
		if user.id == ctx.message.author.id:
			cpDefault = user.cpDefault
			for k, v in user.cpFilters.items():
				outputMessage = outputMessage + k + ":" + str(v) + ", "
			break
	if len(outputMessage) == 0: outputMessage = "No CP filters found."
	
	outputMessage = outputMessage.strip(', ')
	outputMessage = "Your default CP filter is: " + str(cpDefault) + "\nYour CP filter list is: " + outputMessage
	
	if len(outputMessage) <= 1960:
		outputMessage = greeting(ctx) + outputMessage
		await symphony.say(outputMessage)
	else:
		over2kMsg = greeting(ctx) + "Your CP filter list is over 2000 characters, sending the results as a direct message."
		await symphony.say(over2kMsg)
		for under2kMsg in splitMessageInto2kChunks(outputMessage):
			await symphony.send_message(ctx.message.author, under2kMsg)	
	
@symphony.event
async def on_message(message):
	global messagesReadPerMinute
	global inputPerMinute
	global feedsSentPerMinute
	global directMessagesSentPerMinute
	messagesReadPerMinute += 1
	
	# we do not want the bot to reply to itself
	if message.author == symphony.user:
		return
	
	# only accept spawn input from the input channel
	if message.channel.id == input.id:
		log("Input received   " + message.id, "time")
		inputPerMinute += 1
		
		# for monocle input
		monocleInput = message.content
		monocleInput = monocleInput[31:len(monocleInput) - 1]
		s = readInput(monocleInput)
		
		#s = readInput(message.content)
		
		# if IV Error send input and output to troubleshooting channel and no where else
		if s.ivTotal == -1:
			await symphony.send_message(troubleshooting, message)
			await symphony.send_message(troubleshooting, embed = s.message)
			return
		
		# send to 'all' channel
		await symphony.send_message(all, embed = s.message)
		log("First feed sent  " + message.id, "time")
		feedsSentPerMinute += 1
		
		# log neighborhood not found to troubleshooting channel
		if (s.locationName == "Neighborhood not found"):
			await symphony.send_message(troubleshooting, message.content)
			await symphony.send_message(troubleshooting, embed = s.message)
			feedsSentPerMinute += 1
		
		if (s.move1Name == "Move not found" or s.move2Name == "Move not found"):
			await symphony.send_message(troubleshooting, message.content)
			await symphony.send_message(troubleshooting, embed = s.message)
			feedsSentPerMinute += 1
		
		subsToHood = findSubcribedUsers(s.locationName)
		try:
			subs = ivFilterOutSubs(subsToHood, s.pokemonName, s.percent)
		except:
			log("iv filter DED")
		try:
			subs = cpFilterOutSubs(subs, s.pokemonName, s.cp)
		except:
			log("cp filter DED")
		
		
		firstDM = True
		for sub in subs:
			try:
				sendToUser = server.get_member(sub.id)
				if firstDM:
					log("First DM sent    " + message.id, "time")
					firstDM = False
				try:
					log("DMing " + sub.name + " " + s.pokemonName + " " + str(s.percent))
				except:
					log("DMing " + sub.id + " " + s.pokemonName + " " + str(s.percent))
				await symphony.send_message(sendToUser, embed = s.message)
				directMessagesSentPerMinute += 1
			except BaseException as e:
				try:
					log("Error DMing " + sub.name + ": " + str(e))
				except:
					log("Error DMing " + sub.id + ": " + str(e))
		
		log("All DMs sent     " + message.id, "time")
		
		
		# --------------------------feeds--------------------------
		# 100 iv
		if (s.ivTotal == 45): 
			await symphony.send_message(perfectIV, embed = s.message)
			feedsSentPerMinute += 1
		# dratini fam	
		if (s.pokemon_id == 147 or s.pokemon_id == 148 or s.pokemon_id == 149):
			await symphony.send_message(dratini, embed = s.message)
			feedsSentPerMinute += 1
		
		# gen 1 & 2 starters
		if (s.pokemon_id >= 1 and s.pokemon_id <= 9) or (s.pokemon_id >= 152 and s.pokemon_id <= 160):
			await symphony.send_message(starters, embed = s.message)
			feedsSentPerMinute += 1
		# cp >= 2500
		if (s.cp >= 2500):
			await symphony.send_message(hugeMons, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id >= 138 and s.pokemon_id <= 142 and s.percent >= 90):
			await symphony.send_message(discord.Object(id = '314253025680293888'), embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id in [74, 75, 76, 95, 111, 112, 185, 213, 219, 246, 247, 248] and s.percent >= 90):
			await symphony.send_message(discord.Object(id = '314253064758624266'), embed = s.message)
			feedsSentPerMinute += 1
		
		# larvitar fam
		if (s.pokemon_id == 246 or s.pokemon_id == 247 or s.pokemon_id == 248):
			await symphony.send_message(larvitar, embed = s.message)
			feedsSentPerMinute += 1
		# others
		if (s.pokemon_id == 131): 
			await symphony.send_message(lapras, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id == 143): 
			await symphony.send_message(snorlax, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id == 88 or s.pokemon_id == 89): 
			await symphony.send_message(grimer, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id == 113 or s.pokemon_id == 242): 
			await symphony.send_message(chansey, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id == 106 or s.pokemon_id == 107 or s.pokemon_id == 237): 
			await symphony.send_message(hitmonchanLeeTop, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id == 179 or s.pokemon_id == 180): 
			await symphony.send_message(mareep, embed = s.message)
			feedsSentPerMinute += 1
		if (s.pokemon_id == 201): 
			await symphony.send_message(unown, embed = s.message)
			feedsSentPerMinute += 1
		# rares: snorlax, lapras, blissey fam, porygon, larvitar fam, dratini fam
		rarePokemonNumbers = [143, 131, 113, 242, 137, 233, 181, 147, 148, 149, 246, 247, 248, 201]
		if (s.pokemon_id in rarePokemonNumbers):
			if ((s.pokemon_id == 147 or s.pokemon_id == 148) and s.percent < 90): return
			if ((s.pokemon_id == 246 or s.pokemon_id == 247) and s.percent < 82): return
			await symphony.send_message(rares, embed = s.message)
			feedsSentPerMinute += 1
		
		log("All feeds sent   " + message.id, "time")
		
	else: 
		if message.channel.id == support.id:
			log("Command received " + message.id, "time")
			await symphony.process_commands(message)
			log("Command finished " + message.id, "time")		
			
		if message.channel.is_private == True:
			log("Command received " + message.id, "time")
			await symphony.process_commands(message)
			log("Command finished " + message.id, "time")
						
pokemonList = loadPokemon()
moveList = loadMoves()	
loadGeoData()
importUsers()
exportTimer()
actionsPerMinuteTimer()
symphony.run("Mjg4NTYwMTI5MTAyNzA4NzM3.C5_mKg.G3lfXpkqnvr8ocJxnfKJ7YPO3pE")
atexit.register(exit_handler)