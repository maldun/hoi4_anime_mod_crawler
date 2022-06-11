# hoi4_anime_mod_crawler
A simple script which crawls through hoi4 anime mods and searches for missing pictures.
Especially in the Linux version files are often missed due to case sensitivity of the file
system.

## Install:
Just copy anime_mod_crawler.py into your hoi4 workshop folder.
This is STEAMFOLDER/steamapps/workshop/content/394360

In Linux this is: ~/.local/share/Steam/steamapps/workshop/content/394360
Prerequisite is an installation of Python (3.6+)

## Usage: 
python anime_mod_crawler.py [-h] mod_id anime_mod_id [anime_mod_id_to_crawl ...]

The script creates a log, a list of files missed and a diff folder which then can be copied 
into the modfolder in questions.

## Examples:
Crawls through Road to Anime to find missing pictures in Road to 56:
`python anime_mod_crawler.py road_to_56 road_to_anime`

Crawls trhought Road to Anime and Anime Historia to find missing pictures and also adds possible suggetions:
`python picture_crawler.py road_to_56 road_to_anime anime_history`

