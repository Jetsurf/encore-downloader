# Encore Downloader
This tool is meant to be used to download all charts that are posted on [enchor.us](https://www.enchor.us/) for use in Clone Hero.

At this time, all charts downloaded are converted using [SngCli](https://github.com/mdsitton/SngFileFormat) from .sng to chart formats compatible with Clone Hero 1.0.0.4080

Once CH 1.1.0 is released and supports .sng format charts, this will be updated to allow direct downloads without conversion.

A GUI for this tool is planned, but has no exact ETA on when it will be completed. For now, this tool must be ran in a cli.

## NOTES - DO NOT SKIP THIS

Allowing this tool to fully download all charts will require roughly 400GB of disk space. If you do not have enough space to accomidate this, it will fill up your disk.

It is HEAVILY recommended to use a new folder separate from your current songs folder to download all the charts too. As ~80,000 new folders will be created,
it will cause working with any other folders in your current songs folder very difficult. 

## Usage

To download, hit "Code" at the top right, then download as a zip and extract it.

### Command Line Options for all OS's

```
  -chf CLONE_HERO_FOLDER, --clone-hero-folder CLONE_HERO_FOLDER
                        Clone Hero songs folder to output charts to. This option is required
  -t THREADS, --threads THREADS
                        Maximum number of threads to allow - defaults to 4 and is recommended
  -td TEMP_DIRECTORY, --temp-directory TEMP_DIRECTORY
                        Temporary directory to use for chart downloads before
                        conversion. Defaults to the 'scratch' folder included in the zip.
  -soe, --stop-on-error
                        Continue on error during conversion or download. Only used for debugging
  -p PAGE, --page PAGE
                        Starting page for Encore downloads - defaults to 1. Only used for debugging
  -s SEARCH, --search SEARCH
                        String entry to search on Encore - defaults to blank string (empty search/all results)
                        Only used for debugging
  -d, --drums
                        Only downloads charts containing drum parts
  -sc, --schema-cleanup
                        Renames downloaded charts to match the naming schema that Bridge uses.
                        Run the script with this flag if you have previously downloaded charts with this
                        script and want to have compatibility with Bridge
  -rp, --remove-playlist
                        Removes "playlist=" and "playlist_track=" lines from the song.ini of every chart.
                        This includes both new downloads, and previously downloaded charts in your directory.
```

### Windows

For convenience, a pre-built .exe file is added in the repository to allow this tool to be ran without setting up a python environment.

`cd C:\Users\yourusername\Downloads\encore-downloader` (if you extract the zip in your downloads folder, replace yourusername with your Windows username. Navigate to where you extracted the tool)

`.\main.exe -chf C:\Users\yourusername\Documents\CloneHero-EncoreSongs` (CloneHero-EncoreSongs being a new folder, add it to Clone Hero once the download is complete)

### Linux

As Linux usually includes python, simply get the requirement libraries added then run it

`pip3 install -r requirements.txt`

`python3 ./main.py -chf /home/yourusername/clonehero/CloneHero-EncoreSongs` (CloneHero-EncoreSongs being a new folder, add it to Clone Hero once the download is complete. Replace yourusername with your linux username)

### macOS

macOS is not tested, but should work assuming you get a python environment setup and working. If issues are found, create an issue to get it corrected.

## Credit

[Geomitron](https://github.com/Geomitron) - [Bridge](https://github.com/Geomitron/Bridge) - The inspiration for this tool, and [enchor.us](https://www.enchor.us/) to make this possible

[Matthew Sitton](https://github.com/mdsitton) - [SngCli](https://github.com/mdsitton/SngFileFormat) - Tool to convert .sng to Clone Hero supported files
