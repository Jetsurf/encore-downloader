import requests, json, asyncio, uuid, aiohttp, sys, argparse, os, platform, subprocess, shutil, unicodedata, re

async def downloadChart(tempFolder, chartFolder, theChart: dict, rzflag) -> str:
	url = f"https://files.enchor.us/{theChart['md5']}{('_novideo','')[not theChart['hasVideoBackground']]}.sng"
	async with aiohttp.ClientSession() as session:
		#changed timeout to include sock_connect and a longer total timeout
		custom_timeout = aiohttp.ClientTimeout(sock_connect=10, total=300)
		try:
			resp = await session.get(url, timeout = custom_timeout)
			if resp.status != 200:
				print(f"Encore returned non-200 status code for chart: {resp.status}")
				return None
			theSng = await resp.content.read()
		except asyncio.TimeoutError:
			print(f"Timeout downloading chart {theChart['name']} {theChart['album']} {theChart['artist']} - {theChart['md5']}")
			return None
		except Exception as e:
			print(f"Error in reading sng chart content: {e}")
			return None

	sngUuid = str(uuid.uuid4())
	#os.path.join() to reduce the number of platform.system() calls, no idea if this is "better", but looks nicer.
	sngScratchDir = os.path.join(tempFolder, sngUuid)
	output = outputChartDir(chartFolder, theChart, rzflag)

	try:
		os.makedirs(sngScratchDir)
		if platform.system() == 'Windows':
			#Make a new directory inside scratch for SngCli.exe to output to
			os.makedirs(f"{sngScratchDir}\\1")
			#change .sng save to just be "chart". This could be named anything, but chart seemed appropriate.
			with open(f"{sngScratchDir}\\chart.sng",'wb') as file:
				file.write(theSng)
		else:
			with open(f"{sngScratchDir}/{output['file']}.sng",'wb') as file:
				file.write(theSng)
	except Exception as e:
		print(f"Error encountered saving download - exception {e}")
		return None

	return sngScratchDir

async def convertChart(tempFolder, chartFolder, theChart, rzflag) -> bool:
	sngCliPath = f".\\SngCli\\SngCli.exe" if platform.system() == 'Windows' else f"SngCli/SngCli"
	try:
		#added variable to change destination of SngCli.exe output on Windows
		if platform.system() == "Windows":
			outputDir = f"{tempFolder}\\1" 
		else:
			outputDir = chartFolder
		proc = subprocess.run(f'{sngCliPath} decode -in "{tempFolder}" -out "{outputDir}" --noStatusBar', check=True, shell=True, stdout=subprocess.DEVNULL)
	except Exception as e:
		print(f"SngCli Decode Failed: {e}")
		return False
	
	#This block performs the making of the final directory moves the decoded charts from the scratch folder (on Windows)
	if platform.system() == "Windows":
		outputFolder = outputChartDir(chartFolder, theChart, rzflag)
		#Making final directory path
		finalChartPath = f"{u'\\\\?\\'}{outputFolder['dir']}"
		os.makedirs(finalChartPath)
		#path of decoded chart in scratch
		fullChartTempPath = f"{tempFolder}\\1\\chart"
		#Moving all items inside scratch to final
		for item in os.listdir(fullChartTempPath):
			source_item = os.path.join(fullChartTempPath, item)
			target_item = os.path.join(finalChartPath, item)
			shutil.move(source_item, target_item)
		#cleanup scratch
		shutil.rmtree(f'{tempFolder}')
	else:
		shutil.rmtree(f'{tempFolder}')
	
	return True

def getEncorePage(page: int) -> dict:
	d = { "search" : "", 'per_page' : 250, 'page' : page }

	resp = requests.post("https://api.enchor.us/search/", data = json.dumps(d), headers = {"Content-Type":"application/json"})
	retJson = resp.json()

	return retJson

def trimPageDuplicates(thePage) -> dict:
	for i, chart1 in enumerate(thePage):
		for j, chart2 in enumerate(thePage):
			if chart1['ordering'] == chart2['ordering'] and i != j:
				del thePage[j]
	return thePage

def outputChartDir(chartFolder, theChart: str, rzflag) -> dict:
	MAX_FILE_LEN = os.pathconf('.', 'PC_NAME_MAX') if platform.system() != "Windows" else 255
	newFile = f"{theChart['artist']} - {theChart['name']} ({theChart['charter']})"
	newFile = newFile.replace("/",  u'\uFF0F') #／
	newFile = newFile.replace("\\", u'\u29F5') #⧵
	newFile = newFile.replace(":",  u'\uA789') #꞉
	newFile = newFile.replace("<",  u'\u276E') #❮
	newFile = newFile.replace(">",  u'\u276F') #❯
	newFile = newFile.replace("\"", u'\u0027') #'
	newFile = newFile.replace("?",  u'\uFF1F') #？
	newFile = newFile.replace("*",  u'\u204E') #⁎
	newFile = newFile.replace("|",  u'\u23D0') #⏐
	newFile = newFile.lstrip()
	if rzflag:
		newFile = newFile.replace(u'\u200b', "")
		newFile = newFile.replace(u'\u200c', "")
	newFile = newFile.strip()

	if platform.system() == 'Windows':
		newFile = newFile[:MAX_FILE_LEN]
		newFile = newFile.rstrip()
		outputDir = f"{chartFolder}\\{newFile}"
	else:
		newFile = newFile[:MAX_FILE_LEN - 4] #-4 for .sng
		outputDir = f'{chartFolder}/{newFile}'

	return { "dir" : outputDir, "file" : newFile }

def oldOutputChartDir(chartFolder, theChart: str, rzflag) -> dict:
	MAX_FILE_LEN = os.pathconf('.', 'PC_NAME_MAX') if platform.system() != "Windows" else 255
	newFile = f"{theChart['artist']} - {theChart['name']} ({theChart['charter']})"
	newFile = newFile.replace("/",  "")
	newFile = newFile.replace("\\", "")
	newFile = newFile.replace(":",  "")
	newFile = newFile.replace("<",  "")
	newFile = newFile.replace(">",  "")
	newFile = newFile.replace("\"", "")
	newFile = newFile.replace("?",  "")
	newFile = newFile.replace("*",  "")
	newFile = newFile.replace("|",  "")
	newFile = newFile.lstrip()
	if rzflag:
		newFile = newFile.replace(u'\u200b', "")
		newFile = newFile.replace(u'\u200c', "")
	newFile = newFile.strip()

	if platform.system() == 'Windows':
		newFile = newFile[:MAX_FILE_LEN]
		newFile = newFile.rstrip()
		outputDir = f"{chartFolder}\\{newFile}"
	else:
		newFile = newFile[:MAX_FILE_LEN - 4] #-4 for .sng
		outputDir = f'{chartFolder}/{newFile}'

	return { "dir" : outputDir, "file" : newFile }

async def doChartDownload(theChart, args, sema):
	async with sema:
		print(f"Starting download/conversion of chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['charter']} - {theChart['md5']}")
		tempFolder = await downloadChart(args.temp_directory, args.clone_hero_folder, theChart, args.remove_zerowidth)
		if not tempFolder:
			print(f"Error downloading chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['md5']}")
			if args.stop_on_error:
				print("Encountered error, and continue error not set, quitting.")
				sys.exit(1)
			else:
				return

		if not await convertChart(tempFolder, args.clone_hero_folder, theChart, args.remove_zerowidth):
			print(f"Error converting chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['md5']}")
			if args.stop_on_error:
				print("Encountered error, and continue error not set, quitting.")
				sys.exit(1)

		if args.remove_playlist:
			#Added OS detection for long path purposes
			chartDir = outputChartDir(args.clone_hero_folder, theChart, args.remove_zerowidth)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, theChart, args.remove_zerowidth)['dir']}"
			if os.path.isfile(os.path.join(chartDir, "song.ini")):
				await removePlaylist(chartDir)

async def removePlaylist(chartDir):
	#os.path.join change here as well (to reduce platform.system() calls)
	fileName = os.path.join(chartDir, "song.ini")
	with open(fileName, encoding='utf-8', mode="r") as file:
		lines = file.readlines()
	with open(fileName, encoding='utf-8', mode='w') as file:
		for line in lines:
			lineTest = line.replace(" ","").strip("\n")
			if "playlist_track=" not in lineTest and "playlist=" not in lineTest:
				file.write(line)

def renameZeroWidthFolders(chFolder):
	#check to cleanup folders containing zero-width spaces
	folders = [f for f in os.listdir(chFolder) if os.path.isdir(os.path.join(chFolder, f))]
	filtered_list = [item for item in folders if u'\u200b' in item or u'\u200c' in item]
	for folder in filtered_list:
		renamedFolder = folder.replace(u'\u200b', "")
		renamedFolder = renamedFolder.replace(u'\u200c', "")
		renamedFolder = renamedFolder.strip()
		oldFolder = os.path.join(chFolder, folder)
		newFolder = os.path.join(chFolder, renamedFolder)
		if platform.system() == "Windows":
			oldFolder = f'{u'\\\\?\\'}{oldFolder}'
			newFolder = f'{u'\\\\?\\'}{newFolder}'
		if os.path.isdir(newFolder):
			shutil.rmtree(f'{oldFolder}')
		else:
			os.rename(oldFolder, newFolder)

def main():
	#I removed winlongpath argument (as well as the code blocks) as it is unnecessary now
	argParser = argparse.ArgumentParser()
	argParser.add_argument("-t", "--threads", help="Maximum number of threads to allow", default=4, type=int)
	argParser.add_argument("-p", "--page", help="Encore download page to start on", default=1, type=int)
	argParser.add_argument("-td", "--temp-directory", help="Temporary directory to use for chart downloads before conversion", default=f"{os.getcwd()}\\scratch" if platform.system() == 'Windows' else "scratch")
	argParser.add_argument("-soe", "--stop-on-error", help="Continue on error during conversion or download", action="store_true")
	argParser.add_argument("-chf", "--clone-hero-folder", help="Clone Hero songs folder to output charts to", required=True)
	argParser.add_argument("-rp", "--remove-playlist", help="Remove playlist data for downloaded charts", action="store_true")
	argParser.add_argument("-rz", "--remove-zerowidth", help="Remove zero-width characters from chart names. Retroactively renames any chart folders that contain zero-width characters.", action="store_true")
	argParser.add_argument("-sc", "--schema-cleanup", help="Deletes folders that do not match Bridge's naming schema", action="store_true")
	args = argParser.parse_args()

	print(f"Outputting charts to folder {args.clone_hero_folder}")
	print(f"Using temp folder {args.temp_directory} for chart downloads")
	print(f"Using {args.threads} threads")
	if args.stop_on_error:
		print("Will stop download/convert of charts on error")
	if args.remove_playlist:
		print("Removing playlist data for charts (downloaded+to-download)")
	if not args.page > 0:
		print("Page argument must be >0!")
		sys.exit(1)
	if args.remove_zerowidth:
		renameZeroWidthFolders(args.clone_hero_folder)

	sema = asyncio.Semaphore(int(args.threads))
	page = args.page
	pageData = getEncorePage(page)
	numCharts = pageData['found']
	pageData = trimPageDuplicates(pageData['data'])
	while(len(pageData) > 0):
		for i, chart in enumerate(pageData):
			chartNum = ((page - 1) * 250) + (i + 1)
			if chartNum % 500 == 0:
				print(f"Progress {chartNum} of {numCharts}")
			#Added OS detection for long path purposes
			if args.schema_cleanup:
				oldDir = oldOutputChartDir(args.clone_hero_folder, chart, True)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{oldOutputChartDir(args.clone_hero_folder, chart, True)['dir']}"
				newDir = outputChartDir(args.clone_hero_folder, chart, True)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, chart, True)['dir']}"
				oldDir2 = oldOutputChartDir(args.clone_hero_folder, chart, False)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{oldOutputChartDir(args.clone_hero_folder, chart, False)['dir']}"
				newDir2 = outputChartDir(args.clone_hero_folder, chart, False)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, chart, False)['dir']}"
				if os.path.isdir(oldDir) and oldDir != newDir:
					shutil.rmtree(oldDir)
				if os.path.isdir(oldDir2) and oldDir2 != newDir2:
					shutil.rmtree(oldDir2)
			chartDir = outputChartDir(args.clone_hero_folder, chart, args.remove_zerowidth)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, chart, args.remove_zerowidth)['dir']}"
			if os.path.isdir(chartDir):
				if args.remove_playlist and os.path.isfile(os.path.join(chartDir, "song.ini")):
					asyncio.run(removePlaylist(chartDir))
				continue

			print(f"Spawning thread for chart download chart {chartNum} out of {numCharts}")
			asyncio.run(doChartDownload(chart, args, sema))

		page += 1
		pageData = trimPageDuplicates(getEncorePage(page)['data'])

if __name__ == '__main__':
	main()
