import discord
from discord.ext import tasks
from discord.ext import commands
import requests
import database
import datetime
import swannybottokens


# ESPN endpoints
# All Sports API https://sports.core.api.espn.com/v2/sports
# Latest Scoreboard API http://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard
# Team Info API http://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/:team
# Game Info API http://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event=:gameId
# Rankings API http://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings

# !fsu;
#

# nextEvent.0.competitions.boxscoreAvailable
# (if this is true, refer to scoreboard api as it is likely going to be more accurate/up to date)

# nextEvent.0.status.type.state
# as an alternate field to use incase boxscore Available isn't reliable

# scoreboard API
# events filtering for a string for Florida State Seminoles in events.i.name and going from there

# !rankings;
# calls up the current rankings using the rankings API
# todo: database initialization/import
# @commands.command(name="sportscogimport", help="creates the sports, league, and team databases.")
# async def sportscogimport(self, ctx)

class sports_cog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dbhandler = database.dbhandler()
		self.whensTheGame.start()
# dbhandler is the cursor
# self.dbhandler.execute , .commit, .insert
	
	

	@tasks.loop(minutes=2)
	#@commands.command(name='wtg')
	async def whensTheGame(self):
		if self.whatsTheScore.is_running():
			self.whatsTheScore.stop()
		currentDate = datetime.datetime.utcnow()
		currentDate = str(currentDate)
		currentDate = currentDate[:10] + "T" + currentDate[11:16]
		todaysTeamName = 'Florida State Seminoles'
		todaysGameId = ''
		todaysGameLink = 'https://www.espn.com/college-football/game/_/gameId/'
		todaysGameTime = ''
		todaysGameDetails = ''
		todaysKickoff = ''
		sbresponse = requests.get("http://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard")
		sbresponse.json()
		scoreboard = sbresponse.json()
		
		# search for the gameid and info for scoringplays for whensthescore
		for i in scoreboard['events']:
			if todaysGameId != '':
				todaysGameLink += todaysGameId
				break
			if todaysTeamName in i['name']:
				todaysGameDetails = i
				todaysGameId = i['competitions'][0]['id']
				todaysGameTime = i['competitions'][0]['date'][:-1]
				todaysTitle = todaysGameDetails['name']
				gameresponse = requests.get(
					"http://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event=" + todaysGameId)
				gameresponse.json()
				todaysGamePlayByPlay = gameresponse.json()
		
		# sometimes ESPN scoreboard is not populated with a particular game, or the team is just not scheduled to play.
		if todaysGameId == '':
			byeWeekResponse = requests.get('http://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/52').json()
			todaysGameDetails = byeWeekResponse['team']['nextEvent'][0]
			todaysGameId = todaysGameDetails['id']
			todaysGameLink += todaysGameId
			todaysTitle = todaysGameDetails['name']
			todaysGameTime = todaysGameDetails['competitions'][0]['date'][:-1]
			gameresponse = requests.get("http://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event=" + todaysGameId)
			gameresponse.json()
			todaysGamePlayByPlay = gameresponse.json()
			
		for i in todaysGamePlayByPlay['boxscore']['teams']:
			if todaysTeamName == i['team']['displayName']:
				todaysTeamColor = discord.Colour.from_str("#" + i['team']['color'])
				todaysLogo = i['team']['logo']
				
		gameDate1 = todaysGamePlayByPlay['header']['competitions'][0]['status']['type']['detail'].upper()
		if 'TBD' in gameDate1:
			pass
		else:
			gameDate1 = gameDate1[:int(gameDate1.find(','))]
		
		gameDate2 = todaysGamePlayByPlay['header']['competitions'][0]['status']['type']['shortDetail']
		
		if 'TBD' in gameDate2:
			gameDate = gameDate1
		else:
			gameDate = gameDate1 + " " + gameDate2[:int(gameDate2.find(' '))]
		
		gameTime = todaysGamePlayByPlay['header']['competitions'][0]['status']['type']['shortDetail'][-12:]
			
		if currentDate >= todaysGameTime and todaysGameDetails['status']['type']['state'] == 'in':
			general = await self.bot.fetch_channel(swannybottokens.swancordgeneral)
			
			todaysKickoff = discord.Embed(
				color=todaysTeamColor,
				title=todaysTitle,
				url=todaysGameLink)
			todaysKickoff.set_thumbnail(url=todaysLogo)
			todaysKickoff.add_field(name='Date', value= gameDate)
	
			if 'TBD' in gameTime:
				pass
			else:
				todaysKickoff.add_field(name='Time', value= gameTime)
			todaysKickoff.set_footer(text=todaysGameId, icon_url='https://espnpressroom.com/us/files/2018/03/App-Icon-iOS-mic-flag-cut-to-shape.png')
			
			threadStart = await general.send(embed=todaysKickoff)
			threadStart = await general.create_thread(name=todaysGameDetails['shortName'] + " | " + gameDate, message=threadStart)
			
			await self.whatsTheScore(threadStart=threadStart)
	
	
	@tasks.loop(minutes=2)
	#@commands.command(name='whatsTheScore', help='whats the fucking score')
	async def whatsTheScore(self, threadStart):
		if self.whensTheGame.is_running():
			self.whensTheGame.cancel()
		currentDate = datetime.datetime.utcnow()
		currentDate = str(currentDate)
		currentDate = currentDate[:10] + "T" + currentDate[11:16]
		todaysTeamName = 'Florida State Seminoles'
		todaysGameId = ''
		todaysGameLink = 'https://www.espn.com/college-football/game/_/gameId/'
		todaysGameTime = ''
		todaysGameDetails = ''
		todaysGameStart = ''
		sbresponse = requests.get("http://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard")
		sbresponse.json()
		scoreboard = sbresponse.json()
		
		# search for the gameid and info for scoringplays for whensthescore
		for i in scoreboard['events']:
			if todaysGameId != '':
				todaysGameLink += todaysGameId
				break
			if todaysTeamName in i['name']:
				todaysGameDetails = i
				todaysGameId = i['competitions'][0]['id']
				todaysGameTime = i['competitions'][0]['date'][:-1]
				todaysTitle = todaysGameDetails['name']
				gameresponse = requests.get(
					"http://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event=" + todaysGameId)
				gameresponse.json()
				todaysGamePlayByPlay = gameresponse.json()
		
		# sometimes ESPN scoreboard is not populated with a particular game, or the team is just not scheduled to play.
		if todaysGameId == '':
			byeWeekResponse = requests.get(
				'http://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/52').json()
			todaysGameDetails = byeWeekResponse['team']['nextEvent'][0]
			#todaysGameId = todaysGameDetails['id']
			todaysGameLink += todaysGameId
			todaysTitle = todaysGameDetails['name']
			todaysGameTime = todaysGameDetails['competitions'][0]['date'][:-1]
			gameresponse = requests.get(
				"http://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event=" + todaysGameId)
			gameresponse.json()
			todaysGamePlayByPlay = gameresponse.json()
		
		PlaysToPrint = todaysGamePlayByPlay['scoringPlays']
		awayTeamName = todaysGamePlayByPlay['boxscore']['teams'][0]['team']['shortDisplayName']
		awayTeamID = todaysGamePlayByPlay['boxscore']['teams'][0]['team']['id']
		homeTeamName = todaysGamePlayByPlay['boxscore']['teams'][1]['team']['shortDisplayName']
		homeTeamID = todaysGamePlayByPlay['boxscore']['teams'][1]['team']['id']
		awayScore = 0
		homeScore = 0
		PBPText = ''
		currentClock = ''
		currentQuarter = ''
		todaysScoringPlay = ''
		
		for i in PlaysToPrint:
			homeScore = i['homeScore']
			awayScore = i['awayScore']
			PBPText = i['text']
			currentClock = i['clock']['displayValue']
			currentQuarter = i['period']['number']
			if currentQuarter == 1:
				currentQuarter = str(currentQuarter)
				currentQuarter += 'st Quarter'
			elif currentQuarter == 2:
				currentQuarter = str(currentQuarter)
				currentQuarter += 'nd Quarter'
			elif currentQuarter == 3:
				currentQuarter = str(currentQuarter)
				currentQuarter += 'rd Quarter'
			elif currentQuarter == 4:
				currentQuarter = str(currentQuarter)
				currentQuarter += 'th Quarter'
			elif currentQuarter == 5:
				currentQuarter = 'Overtime'
			else:
				currentQuarter = currentQuarter - 4
				currentQuarter = str(currentQuarter)
				currentQuarter = f'{currentQuarter}OT'
				
			if homeTeamID == i['team']['id']:
				embedTitle = f'{homeTeamName} Scoring Play'
				embedColor = discord.Colour.from_str("#" + todaysGamePlayByPlay['boxscore']['teams'][1]['team']['color'])
				embedThumb = todaysGamePlayByPlay['boxscore']['teams'][1]['team']['logo']
				if i['homeScore'] > i['awayScore']:
					summaryText = f'{homeTeamName} now lead {homeScore} - {awayScore}.'
				elif i['homeScore'] == i['awayScore']:
					summaryText = f'{homeTeamName} and {awayTeamName} are now all tied up at {homeScore} - {awayScore}.'
				else:
					summaryText = f'{homeTeamName} are still trailing {homeScore} - {awayScore}.'
					
			if awayTeamID == i['team']['id']:
				embedTitle = f'{awayTeamName} Scoring Play'
				embedColor = discord.Colour.from_str("#" + todaysGamePlayByPlay['boxscore']['teams'][0]['team']['color'])
				embedThumb = todaysGamePlayByPlay['boxscore']['teams'][0]['team']['logo']
				if i['awayScore'] > i['homeScore']:
					summaryText = f'{awayTeamName} now lead {awayScore} - {homeScore}.'
				elif i['homeScore'] == i['awayScore']:
					summaryText = f'{awayTeamName} and {homeTeamName} are now all tied up at {homeScore} - {awayScore}.'
				else:
					summaryText = f'{awayTeamName} are still trailing {awayScore} - {homeScore}.'
			
			todaysScoringPlay = discord.Embed(
				color=embedColor,
				title=embedTitle,
				url=todaysGameLink,
				description= PBPText + "\n" + summaryText
				)
			
			todaysScoringPlay.set_footer(text=todaysGameId, icon_url='https://espnpressroom.com/us/files/2018/03/App-Icon-iOS-mic-flag-cut-to-shape.png')
			
			if 'Overtime' in currentQuarter:
				pass
			elif 'OT' in currentQuarter:
				pass
			else:
				todaysScoringPlay.add_field(name='Clock', value=currentClock)
				
			todaysScoringPlay.add_field(name='Period', value=currentQuarter)
			todaysScoringPlay.set_thumbnail(url=embedThumb)
			
			await threadStart.send(embed=todaysScoringPlay)
			
	
		if todaysGamePlayByPlay['header']['competitions'][0]['status']['type']['state'] == 'post':
			if homeScore > awayScore:
				embedColor = discord.Colour.from_str("#" + todaysGamePlayByPlay['boxscore']['teams'][1]['team']['color'])
				embedThumb = todaysGamePlayByPlay['boxscore']['teams'][1]['team']['logo']
				
				if 'Overtime' in currentQuarter:
					embedTitle = f'{homeTeamName} defeat {awayTeamName} at home in {currentQuarter}, {homeScore} - {awayScore}.'
				elif 'OT' in currentQuarter:
					embedTitle = f'{homeTeamName} defeat {awayTeamName} at home in {currentQuarter}, {homeScore} - {awayScore}.'
				else:
					embedTitle = f'{homeTeamName} defeat {awayTeamName} at home, {homeScore} - {awayScore}.'
				
			else:
				embedColor = discord.Colour.from_str("#" + todaysGamePlayByPlay['boxscore']['teams'][0]['team']['color'])
				embedThumb = todaysGamePlayByPlay['boxscore']['teams'][0]['team']['logo']
				
				if 'Overtime' in currentQuarter:
					embedTitle = f'{awayTeamName} defeat {homeTeamName} on the road in {currentQuarter}, {awayScore} - {homeScore}.'
				elif 'OT' in currentQuarter:
					embedTitle = f'{awayTeamName} defeat {homeTeamName} on the road in {currentQuarter}, {awayScore} - {homeScore}.'
				else:
					embedTitle = f'{awayTeamName} defeat {homeTeamName} on the road, {awayScore} - {homeScore}.'
			
			
			todaysFinalScore = discord.Embed(
				color=embedColor,
				title=embedTitle,
				url=todaysGameLink
				)
			todaysFinalScore.set_thumbnail(url=embedThumb)
			todaysFinalScore.set_footer(text=todaysGameId, icon_url='https://espnpressroom.com/us/files/2018/03/App-Icon-iOS-mic-flag-cut-to-shape.png')
		
		await threadStart.send(embed=todaysFinalScore)
		self.whensTheGame.start()

	# todo: DB CREATE (initializing table values) uuid (fixed), uid, teamid, spo rtsid, leagueid, location, name
	# todo: DB INSERT (!sportslurp)
	#	https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/teams?limit=1000
	
	@commands.command(name="fsu", help="Sends a message with a summary of a team's season.")
	async def fsu(self, ctx):
		# initialize shit
		currentDate = datetime.datetime.utcnow()
		currentDate = str(currentDate)
		currentDate = currentDate[:10] + "T" + currentDate[11:16]
		teamid = '52'
		teamresponse = requests.get(
			"http://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/" + teamid)
		teamresponse.json()
		teamRawData = teamresponse.json()
		teamDict = teamRawData['team']
		teamColor = discord.Colour.from_str("#" + teamDict['color'])
		teamRecord = teamDict['record']['items'][0]['summary']
		uid = teamDict['uid']
		
		# grabbing uids for sport, league, team to initialize other variables with and be faster
		# I think I did this efficiently enough
		databaseSportId = uid[int(uid.find('s')):int(uid.find('~'))]
		databaseLeagueId = uid[int(uid.find('l')):int(uid.find('~', 5))]
		databaseTeamId = uid[10:]
		
		# todo: initialize teamSport, teamLeague by looking through referencing SportLeague table
		#   find a way to call each individual sport in this link
		#       https://sports.core.api.espn.com/v2/sports
		#           SPORT - pull id, uid, name, slug
		#   each individual sport should also have a set of leagues
		#       http://sports.core.api.espn.com/v2/sports/football/leagues
		#           LEAGUE - pull id, uid, abbreviation, midsizeName, slug
		#   each individual league should also have a set of teams
		#       http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2023/teams
		#           TEAM - pull id, uid, abbreviation, location, name, displayName, color
		#   -
		#   SELECT * FROM Sports_Espn_TABLENAME
		
		teamSport = "Football"
		teamLeague = "DI-A (FBS)"
		currentYear = datetime.datetime.utcnow()
		currentYear = str(currentDate)
		currentYear = currentDate[:4]
		seasonresponse = requests.get(f"http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{currentYear}/teams/" + teamid)
		seasonresponse.json()
		seasonRawData = seasonresponse.json()
		teamVenue = seasonRawData['venue']['fullName']
		
		scheduleresponse = requests.get(f'http://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{currentYear}/teams/' + teamid + "/events")
		scheduleresponse.json()
		scheduleRawData = scheduleresponse.json()
		
		gameRecap = ""
		gameWeek = 1
		gameHomeScore = ''
		gameAwayScore = ''
		gameDate = ''
		gameOpponent = ''
		for i in scheduleRawData['items']:
			gameid = i['$ref']
			gameid = gameid[int(gameid.find("4")):int(gameid.find("?"))]
			gameresponse = requests.get(i['$ref'])
			gameresponse.json()
			gameRawData = gameresponse.json()
			
			if gameRawData['competitions'][0]['recapAvailable'] is True:
				pass
			elif gameRawData['competitions'][0]['summaryAvailable'] is True:
				gameDate = gameRawData['date'][:-1]
				if gameDate > currentDate:
					break
				else:
					pass
			else:
				break
			
			if gameRawData['competitions'][0]['competitors'][0]['id'] == teamid:
				try:
					gameWin = gameRawData['competitions'][0]['competitors'][0]['winner']
					gameOpponent = gameRawData['name']
					gameOpponent = " vs. " + gameOpponent[:int(gameOpponent.find(" at"))]
				except:
					gameHomeScoreData = gameRawData['competitions'][0]['competitors'][0]['score']
					gameHomeScoreData = requests.get(gameHomeScoreData['$ref'])
					gameHomeScoreData.json()
					gameHomeScoreData = gameHomeScoreData.json()
					gameHomeScore = gameHomeScoreData['displayValue']
			else:
				gameWin = gameRawData['competitions'][0]['competitors'][1]['winner']
				gameOpponent = gameRawData['name']
				gameOpponent = " @ " + gameOpponent[int(gameOpponent.find(" ", int(gameOpponent.find(" at")))):]
				
			
			
			if gameWin == True:
				gameWin = 'W'
			else:
				gameWin = 'L'
			
			gameRecap = gameRecap + "Week " + str(gameWeek) + " - " + gameWin + gameOpponent + "\n"
			
			gameWeek = gameWeek + 1
		
		nextGame = teamDict['nextEvent'][0]['week']['text'] + "\n"
		nextDate = teamDict['nextEvent'][0]['competitions'][0]['status']['type']['shortDetail']
		gameVenue = ""
		nextOpponent = ""
		
		if teamDict['nextEvent'][0]['competitions'][0]['competitors'][0]['id'] == teamid:
			gameVenue = teamVenue
			nextOpponent = "vs. " + teamDict['nextEvent'][0]['competitions'][0]['competitors'][1]['team'][
				'displayName']
		else:
			gameVenue = teamDict['nextEvent'][0]['competitions'][0]['venue']['fullName']
			nextOpponent = "@ " + teamDict['nextEvent'][0]['competitions'][0]['competitors'][0]['team'][
				'displayName']
		
		gameVenue = gameVenue[:int(gameVenue.find("("))]
		gameVenue += "\n" + teamDict['nextEvent'][0]['competitions'][0]['venue']['address']['city'] + ", " + \
					 teamDict['nextEvent'][0]['competitions'][0]['venue']['address']['state']
		
		# if the team has been labelled active but has a blank value listed for nextEvent (case for t:53 Florida Tech)
		# todo: end of season buddy, try again next year.
		if teamDict['isActive'] == True:
			confStatus = teamDict['standingSummary']
		else:
			confStatus = ""
			nextGame = "There might not be a next game."
			nextDate = "Is this team still active?"
		
		# checks if the rank value is on a given teams' page in college sports.
		# todo: enclose in another if statement that checks the uid/leagueid to make sure this is relevant
		if 'rank' in teamDict:
			teamRank = "No." + str(teamDict['rank'])
		
		else:
			if teamDict['isActive'] == True:
				teamRank = "NR"
			else:
				teamRank = ""
		
		# I made this I do what I want
		if teamDict['uid'] == "s:20~l:23~t:52":
			uid = "s:20~l:23~t:52 GO NOLES BITCH"
		
		# outlining how the rich embed should look for the !fsu soon to be !sports embed
		prettyMessage = discord.Embed(
			color=int(teamColor),
			title=teamDict['displayName'] + " " + teamSport,
			url=teamDict['links'][0]['href'],
			description=gameRecap + "\n" + "Upcoming:" + "\n" + nextGame + nextOpponent + "\n" + gameVenue + "\n" + nextDate
		)
		prettyMessage.set_thumbnail(url="https://a3.espncdn.com/redesign/assets/img/icons/ESPN-icon-football-college.png")
		prettyMessage.set_image(url=teamDict['logos'][0]['href'])
		prettyMessage.set_footer(text=uid,icon_url='https://espnpressroom.com/us/files/2018/03/App-Icon-iOS-mic-flag-cut-to-shape.png')
		prettyMessage.add_field(name='League', value=teamLeague, inline=True)
		
		if "Division" in teamLeague:
			prettyMessage.add_field(name='AP Rank', value=teamRank, inline=True)
		
		prettyMessage.add_field(name='Conf Rank', value=confStatus, inline=True)
		prettyMessage.add_field(name='Record', value=teamRecord, inline=True)
		
		await ctx.reply(embed=prettyMessage)
	