 # -*- coding: utf-8 -*-

from os import listdir, walk, makedirs, getcwd
from os.path import join, expanduser, split, isfile
from shutil import copy
import argparse
import logging


logging.basicConfig(filename='crawler.log', encoding='utf-8', level=logging.DEBUG)

HOI4_ID = 394360
ROAD_TO_56_ID = 820260968
ROAD_ANIME_ID = 2129060088
ANIME_HISTORY_ID = 1862018480

tag_list = {"road_to_56": ROAD_TO_56_ID,
            "road_to_anime": ROAD_ANIME_ID,
            "anime_history": ANIME_HISTORY_ID,
            }

GFX_PATH = 'gfx'
FOLDERS_TO_CRAWL = {'leaders'}

parser = argparse.ArgumentParser(description='Find missing files. Supported Mod tags: \n'
                                 + ', '.join(tag_list.keys()))
parser.add_argument('mod_id', metavar='mod_id', type=str, nargs=1,
                    help='Main mod to look at')
parser.add_argument('anime_mod_id', metavar='anime_mod_id', type=str, nargs=1,
                    help='Anime mod to look at')
parser.add_argument('anime_mod_id_to_crawl', metavar='anime_mod_id_to_crawl',
                    type=str, nargs='*', help='Anime mod to crawl', default=[],
                    )

arguments = parser.parse_args()

#base = expanduser('~/.local/share/Steam/steamapps/workshop/content/')
#hoi4_path = join(base, str(HOI4_ID))
hoi4_path = getcwd()


def same_name(file1, file2):
    if file1.lower() == file2.lower():
        return True
    return False


def contains_name(file1, file2):
    parts = file1.split('_')
    file1 = '_'.join(parts[-2:])
    if file1.lower() in file2.lower():
        return True
    return False


class ModCrawler:
    def __init__(self, mod_id, anime_mod_id,
                 missing_list_file="missing_items.txt",
                 file_type='.dds',out_folder="diff"):
        """
        Set paths for mod and anime mod.
        """
        self.mod_id = mod_id
        self.anime_mod_id = anime_mod_id
        self.file_type = file_type
        self.out_folder = out_folder
        self.missing = open(missing_list_file, 'w')

    def __del__(self):
        """
        Close file after use
        """
        self.missing.close()

    def crawl(self, anime_mod_id_to_crawl=None, suff='', write=True, criteria=same_name):
        if anime_mod_id_to_crawl is None:
            anime_mod_id_to_crawl = self.anime_mod_id
        org_mod_path = join(hoi4_path, str(self.mod_id))
        for root, folders, files in walk(org_mod_path):
            for file in files:
                self.find_replacement(root, file, anime_mod_id_to_crawl,
                                      suff=suff, write=write,criteria=criteria)

    def find_replacement(self, root, file, anime_mod_id_to_crawl,
                         criteria=same_name, suff='', write=True):
        if (file.endswith(self.file_type) and
                not self.check_if_file_there(root, file, anime_mod_id_to_crawl)):
            root2, file2 = self.find_alternative(
                root, file, same_name, anime_mod_id_to_crawl)
            if root2 is not None:
                # Write to file
                if write is True:
                    self.missing.write(
                        join(root.replace(hoi4_path, ""), file)+'\n')
                # copy file
                self.copy_file(file, root2, file2, suff, anime_mod_id_to_crawl)

    def check_if_file_there(self, root, file, anime_mod_id=None):
        """
        file checks if the given file, is also in the anime mod
        (with given mod id)
        """
        if anime_mod_id is None:
            anime_mod_id = self.anime_mod_id
            
        aroot = root.replace(str(self.mod_id), str(anime_mod_id))
        afpath = join(aroot, file)
        if isfile(afpath):
            return True
        return False

    def remove_suffix(self, fname):
        return fname[:-len(self.file_type)]
    
    def find_alternative(self, root1, file1, criteria, anime_mod_id=None):
        """
        searches for a suitable replacement in a mod for a certain criteria.
        A criteria is a function which compares the two files and return True
        if it is fit.
        """
        if anime_mod_id is None:
            anime_mod_id = self.anime_mod_id

        rfile1 = self.remove_suffix(file1)
        anime_mod_path = join(hoi4_path, str(anime_mod_id))
        
        for root2, folders2, files2 in walk(anime_mod_path):
            for file2 in files2:
                if not file2.endswith(self.file_type):
                    continue
                rfile2 = self.remove_suffix(file2)
                if criteria(rfile1, rfile2) is True:
                    logging.info(f"Found {root2}{file2} as alternative to {root2}{file1}\n")
                    return root2, file2

        return None, None
                
    def copy_file(self, org_file, found_root, found_file, suff, anime_mod_id_to_crawl,
                  temp_root=None, anime_mod_id=None):
        """
        Copies file (currently to copy folder)
        """
        if anime_mod_id is None:
            anime_mod_id = self.anime_mod_id

        if temp_root is None:
            temp_root = found_root.replace(str(anime_mod_id_to_crawl),
                                           self.out_folder + str(anime_mod_id))

        logging.info(f"Copied {found_root}{found_file} to {temp_root}{org_file}\n")
        makedirs(temp_root, exist_ok=True)
        if isfile(join(temp_root, org_file)):
            org_file2 = org_file.replace(self.file_type, suff+self.file_type)
        else:
            org_file2 = org_file
        copy(join(found_root, found_file), join(temp_root, org_file2))


mod_id = arguments.mod_id[0]
anime_mod_id = arguments.anime_mod_id[0]
anime_mod_ids_to_crawl = [anime_mod_id]
if len(arguments.anime_mod_id_to_crawl) > 0:
    anime_mod_ids_to_crawl += arguments.anime_mod_id_to_crawl

if mod_id in tag_list.keys():
    mod_id = tag_list[mod_id]
if anime_mod_id in tag_list.keys():
    anime_mod_id = tag_list[anime_mod_id]
anime_mod_ids_to_crawl = [tag_list[mid] if mid in tag_list.keys() else mid
                          for mid in anime_mod_ids_to_crawl]
crawler = ModCrawler(mod_id, anime_mod_id)


def test_if_file_there():
    root1 = '/home/maldun/.local/share/Steam/steamapps/workshop/content/394360/820260968/gfx/interface/techtree'
    file1 = 'techtree_tank_tab.dds'
    assert crawler.check_if_file_there(root1, file1) is True


TEST = False
if TEST:
    test_if_file_there()

if __name__ == "__main__":
    logging.info("Crawl {}\n".format(anime_mod_id))
    crawler.crawl()
    for k, mid in enumerate(anime_mod_ids_to_crawl):
        logging.info("Lax Crawl {} Mod Nr:{}\n".format(mid, k))
        crawler.crawl(anime_mod_id_to_crawl=mid,
                      suff=f"_v{k}", write=False,
                      criteria=contains_name)
