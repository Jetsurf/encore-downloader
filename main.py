import requests, json, asyncio, uuid, aiohttp, sys, argparse, os, platform, subprocess, shutil, unicodedata, re

async def downloadChart(tempFolder, chartFolder, theChart: dict, rzflag) -> str:
	url = f"https://files.enchor.us/{theChart['md5']}{('_novideo','')[not theChart['hasVideoBackground']]}.sng"
	async with aiohttp.ClientSession() as session:
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
	sngScratchDir = os.path.join(tempFolder, sngUuid)
	output = outputChartDir(chartFolder, theChart, rzflag)

	try:
		os.makedirs(sngScratchDir)
		os.makedirs(f"{sngScratchDir}\\1")
		with open(f"{sngScratchDir}\\chart.sng",'wb') as file:
			file.write(theSng)
		
	except Exception as e:
		print(f"Error encountered saving download - exception {e}")
		return None

	return sngScratchDir

async def convertChart(tempFolder, chartFolder, theChart, rzflag) -> bool:
	sngCliPath = f".\\SngCli\\SngCli.exe" if platform.system() == 'Windows' else f"SngCli/SngCli"
	try:
		outputDir = os.path.join(tempFolder,"1")
		proc = subprocess.run(f'{sngCliPath} decode -in "{tempFolder}" -out "{outputDir}" --noStatusBar', check=True, shell=True, stdout=subprocess.DEVNULL)
	except Exception as e:
		print(f"SngCli Decode Failed: {e}")
		return False
	
	outputFolder = outputChartDir(chartFolder, theChart, rzflag)
	if platform.system() == "Windows":
		finalChartPath = f"{u'\\\\?\\'}{outputFolder['dir']}"
	else:
		finalChartPath = outputFolder["dir"]
	os.makedirs(finalChartPath)
	fullChartTempPath = os.path.join(tempFolder,"1","chart")
	for item in os.listdir(fullChartTempPath):
		source_item = os.path.join(fullChartTempPath, item)
		target_item = os.path.join(finalChartPath, item)
		shutil.move(source_item, target_item)
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

	encoding = 'utf-8'
	bytes_data = newFile.encode(encoding)
	sliced_bytes = bytes_data[:MAX_FILE_LEN]
	newFile = sliced_bytes.decode(encoding, errors='ignore')
	newFile = newFile.rstrip()
	outputDir = f"{chartFolder}\\{newFile}"
    
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
			chartDir = outputChartDir(args.clone_hero_folder, theChart, args.remove_zerowidth)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, theChart, args.remove_zerowidth)['dir']}"
			if os.path.isfile(os.path.join(chartDir, "song.ini")):
				await removePlaylist(chartDir)

async def removePlaylist(chartDir):
	fileName = os.path.join(chartDir, "song.ini")
	with open(fileName, encoding='utf-8', mode="r") as file:
		lines = file.readlines()
	with open(fileName, encoding='utf-8', mode='w') as file:
		for line in lines:
			lineTest = line.replace(" ","").strip("\n")
			if "playlist_track=" not in lineTest and "playlist=" not in lineTest:
				file.write(line)

def renameZeroWidthFolders(chFolder):
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
			shutil.rmtree(oldFolder)
		else:
			shutil.move(oldFolder, newFolder)
			shutil.rmtree(oldFolder)

def schemaRename(chFolder, theChart):
	if platform.system != "Windows":
		oldDir = oldOutputChartDir(chFolder, theChart, False)['dir']
		newDir = outputChartDir(chFolder, theChart, False)['dir']
		oldDirRZ = oldOutputChartDir(chFolder, theChart, True)['dir']
		newDirRZ = outputChartDir(chFolder, theChart, True)['dir']
	else:
		oldDir = f"{u'\\\\?\\'}{oldOutputChartDir(chFolder, theChart, False)['dir']}"
		newDir = f"{u'\\\\?\\'}{outputChartDir(chFolder, theChart, False)['dir']}"
		oldDirRZ = f"{u'\\\\?\\'}{oldOutputChartDir(chFolder, theChart, True)['dir']}"
		newDirRZ = f"{u'\\\\?\\'}{outputChartDir(chFolder, theChart, True)['dir']}"
	if os.path.isdir(oldDir) and oldDir != newDir:
		print(f'Renaming improperly named chart folder: {oldDir}')
		shutil.move(oldDir,newDir)
	if os.path.isdir(oldDirRZ) and oldDirRZ != newDirRZ:
		print(f'Renaming improperly named chart folder: {oldDirRZ}')
		shutil.move(oldDirRZ,newDirRZ)

def main():
	argParser = argparse.ArgumentParser()
	argParser.add_argument("-t", "--threads", help="Maximum number of threads to allow", default=4, type=int)
	argParser.add_argument("-p", "--page", help="Encore download page to start on", default=1, type=int)
	argParser.add_argument("-td", "--temp-directory", help="Temporary directory to use for chart downloads before conversion", default=f"{os.getcwd()}\\scratch" if platform.system() == 'Windows' else "scratch")
	argParser.add_argument("-soe", "--stop-on-error", help="Continue on error during conversion or download", action="store_true")
	argParser.add_argument("-chf", "--clone-hero-folder", help="Clone Hero songs folder to output charts to", required=True)
	argParser.add_argument("-rp", "--remove-playlist", help="Remove playlist data for downloaded charts", action="store_true")
	argParser.add_argument("-rz", "--remove-zerowidth", help="BREAKS BRIDGE COMPATIBILITY! Removes zero-width characters from chart names. Retroactively renames any chart folders that contain zero-width characters.", action="store_true")
	argParser.add_argument("-sc", "--schema-cleanup", help="Renames folders that do not match Bridge's naming schema", action="store_true")
	args = argParser.parse_args()

	print(f"Outputting charts to folder {args.clone_hero_folder}")
	print(f"Using temp folder {args.temp_directory} for chart downloads")
	print(f"Using {args.threads} threads")
	if not args.page > 0:
		print("Page argument must be >0!")
		sys.exit(1)
	if args.stop_on_error:
		print("Will stop download/convert of charts on error")
	if args.remove_playlist:
		print("Removing playlist data for charts (downloaded+to-download)")
	if args.remove_zerowidth:
		print("Removing zero-width characters from chart folder names (downloaded+to-download)")
		renameZeroWidthFolders(args.clone_hero_folder)
	if args.schema_cleanup:
		print("Renaming old chart folders to new naming schema")

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
			if args.schema_cleanup:
				schemaRename(args.clone_hero_folder, chart)
			oldChartDir = oldOutputChartDir(args.clone_hero_folder, chart, args.remove_zerowidth)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{oldOutputChartDir(args.clone_hero_folder, chart, args.remove_zerowidth)['dir']}"
			chartDir = outputChartDir(args.clone_hero_folder, chart, args.remove_zerowidth)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, chart, args.remove_zerowidth)['dir']}"
			if os.path.isdir(chartDir) or os.path.isdir(oldChartDir):
				if args.remove_playlist and os.path.isfile(os.path.join(chartDir, "song.ini")):
					asyncio.run(removePlaylist(chartDir))
				elif args.remove_playlist and os.path.isfile(os.path.join(oldChartDir, "song.ini")):
					asyncio.run(removePlaylist(oldChartDir))
				continue

			print(f"Spawning thread for chart download chart {chartNum} out of {numCharts}")
			asyncio.run(doChartDownload(chart, args, sema))

		page += 1
		pageData = trimPageDuplicates(getEncorePage(page)['data'])

if __name__ == '__main__':
	main()
