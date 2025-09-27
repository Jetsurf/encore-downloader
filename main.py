import requests, json, asyncio, uuid, aiohttp, sys, argparse, os, platform, subprocess, shutil, unicodedata, re

async def downloadChart(tempFolder, chartFolder, theChart: dict) -> str:
	url = f"https://files.enchor.us/{theChart['md5']}{('_novideo','')[not theChart['hasVideoBackground']]}.sng"
	async with aiohttp.ClientSession() as session:
		try:
			resp = await session.get(url, timeout = 10)
		except asyncio.TimeoutError:
			print(f"Timeout downloading chart {theChart['name']} {theChart['album']} {theChart['artist']} - {theChart['md5']}")
			return None

		if resp.status != 200:
			print(f"Ecore returned non-200 status code for chart: {resp.status}")
			return None

		try:
			theSng = await resp.content.read()
		except Exception as e:
			print(f"Error in reading sng chart content: {e}")
			return None

	sngUuid = str(uuid.uuid4())
	sngScratchDir = f"{tempFolder}/{sngUuid}"
	output = outputChartDir(chartFolder, theChart)
	
	try:
		os.makedirs(sngScratchDir)
		with open(f"{sngScratchDir}/{output['file']}.sng",'wb') as file:
			file.write(theSng)
	except Exception as e:
		print(f"Error encountered saving download - exception {e}")
		return None

	return sngScratchDir

async def convertChart(tempFolder, chartFolder, theChart) -> bool:
	sngCliPath = f'.\\SngCli\\SngCli.exe' if platform.system() == 'Windows' else f'SngCli/SngCli'

	try:
		proc = subprocess.run(f'{sngCliPath} decode -in "{tempFolder}" -out "{chartFolder}" --noStatusBar', check=True, shell=True, stdout=subprocess.DEVNULL)
	except Exception as e:
		print(f"SngCli Decode Failed: {e}")
		return False

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

def outputChartDir(chartFolder, theChart: str) -> dict:
	newFile = f"{theChart['artist']} - {theChart['name']} ({theChart['charter']})"
	newFile = newFile.replace("/", "")
	newFile = newFile.replace("\\", "")
	newFile = newFile.replace(":", "")
	newFile = newFile.replace("<", "")
	newFile = newFile.replace(">", "")
	newFile = newFile.replace("\"", "")
	newFile = newFile.replace("?", "")
	newFile = newFile.replace("*", "")
	newFile = newFile.rstrip()
	newFile = newFile[:os.pathconf('.', 'PC_NAME_MAX') - 4] #-4 for .sng

	if platform.system() == 'Windows':
		outputDir = f"{chartFolder}\\{newFile}"[:os.pathconf('.', 'PC_PATH_MAX') - len(newFile)]
	else:
		outputDir = f'{chartFolder}/{newFile}'[:os.pathconf('.', 'PC_PATH_MAX' ) - len(newFile)]

	return { "dir" : outputDir, "file" : newFile }

async def doChartDownload(theChart, args, sema):
	async with sema:
		print(f"Starting download/conversion of chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['charter']} - {theChart['md5']}")
		tempFolder = await downloadChart(args.temp_directory, args.clone_hero_folder, theChart)
		if not tempFolder:
			print(f"Error downloading chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['md5']}")
			if args.stop_on_error:
				print("Encountered error, and continue error not set, quitting.")
				sys.exit(1)
			else:
				return

		if not await convertChart(tempFolder, args.clone_hero_folder, theChart):
			print(f"Error converting chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['md5']}")
			if args.stop_on_error:
				print("Encountered error, and continue error not set, quitting.")
				sys.exit(1)
def main():
	argParser = argparse.ArgumentParser()
	argParser.add_argument("-t", "--threads", help="Maximum number of threads to allow", default=4, type=int)
	argParser.add_argument("-td", "--temp-directory", help="Temporary directory to use for chart downloads before conversion", default="scratch")
	argParser.add_argument("-soe", "--stop-on-error", help="Continue on error during conversion or download", action="store_true")
	argParser.add_argument("-chf", "--clone-hero-folder", help="Clone Hero songs folder to output charts to", required=True)
	args = argParser.parse_args()

	print(f"Outputting charts to folder {args.clone_hero_folder}")
	print(f"Using temp folder {args.temp_directory} for chart downloads")
	print(f"Using {args.threads} threads")
	if args.stop_on_error:
		print("Will stop download/convert of charts on error")

	sema = asyncio.Semaphore(int(args.threads))
	page = 1
	pageData = getEncorePage(page)
	numCharts = pageData['found']
	pageData = trimPageDuplicates(pageData['data'])
	while(len(pageData) > 0):
		for i, chart in enumerate(pageData):
			chartNum = ((page - 1) * 250) + (i + 1)
			if chartNum % 500 == 0:
				print(f"Progress {chartNum} of {numCharts}")
			if os.path.isdir(outputChartDir(args.clone_hero_folder, chart)['dir']):
				continue

			print(f"Spawning thread for chart download chart {chartNum} out of {numCharts}")
			asyncio.run(doChartDownload(chart, args, sema))

		page += 1
		pageData = trimPageDuplicates(getEncorePage(page)['data'])

if __name__ == '__main__':
	main()
