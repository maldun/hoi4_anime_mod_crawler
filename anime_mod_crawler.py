 # -*- coding: utf-8 -*-

from sys import exit
from os import walk, makedirs, getcwd, sep
from os.path import join, expanduser, split, isfile
from shutil import copy
import argparse
import logging
import re


logging.basicConfig(filename='crawler.log', encoding='utf-8', level=logging.DEBUG)

HOI4_ID = 394360
# MAin Mods
ROAD_TO_56_ID = 820260968
KAISERREICH_ID = 1521695605
KAISERREDUX_ID = 2076426030
# Anime Mods
ROAD_ANIME_ID = 2129060088
ANIME_HISTORY_ID = 1862018480
MOEREICH_ID = 1821967568
MOEREDUX_ID = 2488199457
ANIME_HISTORIA_ID = 2224569708


tag_list = {"road_to_56": ROAD_TO_56_ID,
            "kaiserreich": KAISERREICH_ID,
            "kaiserredux": KAISERREDUX_ID,
            "road_to_anime": ROAD_ANIME_ID,
            "anime_history": ANIME_HISTORY_ID,
            "moereich": MOEREICH_ID,
            "moeredux": MOEREDUX_ID,
            "anime_historia": ANIME_HISTORIA_ID
            }

GFX_PATH = 'gfx'
FOLDERS_TO_CRAWL = {'leaders'}
ROLES = ['leaders', 'ministers', 'advisors']
MISC_KEY = 'misc'
desc = 'Find missing files. Supported Mod tags: \n'
desc += ', '.join(tag_list.keys()) 
desc += " (if the tag is not listed just provide the id as number)"

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('mod_id', metavar='mod_id', type=str, nargs=1,
                    help='Main mod to look at')
parser.add_argument('anime_mod_id', metavar='anime_mod_id', type=str, nargs=1,
                    help='Anime mod to look at')
parser.add_argument('anime_mod_id_to_crawl', metavar='anime_mod_id_to_crawl',
                    type=str, nargs='*',
                    help='''Anime mod(s) to crawl. Either one or several. 
                    If none is given anime_mod_id is used''',
                    default=[],
                    )
arguments = parser.parse_args()

# base = expanduser('~/.local/share/Steam/steamapps/workshop/content/')
# hoi4_path = join(base, str(HOI4_ID))
hoi4_path = getcwd()


def same_name(file1, file2, root1=None, root2=None):
    if file1.lower() == file2.lower():
        return True
    return False


def contains_name(file1, file2, root1=None, root2=None):
    if root1 is not None and root2 is not None:
        for role in ROLES: 
            if role in root2:
                if role not in root1:
                    return False
    
    parts = file1.split('_')
    if parts[-2].lower() in {'von', 'van', 'de', 'ter', 'du'}:
        file1 = '_'.join(parts[-3:])
    else:
        file1 = '_'.join(parts[-2:])
    if file1.lower() in file2.lower():
        return True
    return False


class PortraitParser:
    def __init__(self, mod_id, file_type='.txt', pfile_type=".dds"):
        self.mod_id = mod_id
        self.mod_path = join(hoi4_path, str(mod_id))
        self.character_path = join(self.mod_path,
                                   "common", "characters")
        self.idea_path = join("gfx", "interface", "ideas")
        self.file_type = file_type
        self.pfile_type = pfile_type

    def set_expressions(self):
        keys = ["small", "large"]
        expr = [f'{var}(\s*)=(\s*)\"(.*)\"' for var in keys]
        return expr

    def parse_file_for_expression(self, filename, expr):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        results = re.findall(expr, content)
        results = [res[-1] for res in results]
        return results

    def remove_suffix(self, fname):
        return fname[:-len(self.file_type)]

    def replace_path(self, path, tag):
        if path.startswith("GFX_idea"):
            path = path.replace("GFX_", self.idea_path)
            path += self.pfile_type
            return path

        if path.startswith("GFX_"):
            rep = join("gfx", "leaders", tag) + sep
            path = path.replace("GFX_", rep)
            path += self.pfile_type
            return path

        return path

    def replace_paths(self, paths, fname):
        tag = self.remove_suffix(fname)
        paths = [self.replace_path(path, tag) for path in paths]
        return paths

    def _portrait_list(self, expr):
        portraits = []
        try:
            files = list(walk(self.character_path))[0][2]
        except:
            logging.info("Character folder is missing.")
            return []
        for file in files:
            full_path = join(self.character_path, file)
            paths = self.parse_file_for_expression(full_path, expr)
            paths = self.replace_paths(paths, file)
            portraits += paths

        return portraits

    def portrait_list(self):
        result = []
        for expr in self.set_expressions():
            portraits = self._portrait_list(expr)
            portraits = [join(hoi4_path, str(self.mod_id), p) for p in portraits]
            result += portraits
        return result

class ModCrawler:
    def __init__(self, mod_id, anime_mod_id,
                 missing_list_file="missing_items.txt",
                 parsed_out_file='parsed_list.txt',
                 diff_file="files_to_add.txt",
                 file_type='.dds',out_folder="diff"):
        """
        Set paths for mod and anime mod.
        """
        self.mod_id = mod_id
        self.anime_mod_id = anime_mod_id
        self.file_type = file_type
        self.out_folder = out_folder
        self.missing = open(missing_list_file, 'w', encoding='utf-8')
        self.parsed_out_file = parsed_out_file
        self.diff_file = diff_file
        self.portrait_parser = PortraitParser(mod_id,
                                              pfile_type=file_type)

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
                         criteria=same_name, suff='', write=True, copy=True):
        if (file.endswith(self.file_type) and
                not self.check_if_file_there(root, file, anime_mod_id_to_crawl)):
            root2, file2 = self.find_alternative(
                root, file, criteria, anime_mod_id_to_crawl)
            if root2 is not None:
                # Write to file
                if write is True:
                    self.missing.write(
                        join(root.replace(hoi4_path, ""), file)+'\n')
                # copy file
                if copy is True:
                    self.copy_file(file, root2, file2, suff, anime_mod_id_to_crawl)
                else:
                    return file, root2, file2

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
                if criteria(rfile1, rfile2, root1, root2) is True:
                    logging.info(f"Found {root2}{file2} as alternative to {root2}{file1}\n")
                    return root2, file2

        return None, None
                
    def copy_file(self, org_file, found_root, found_file, suff, anime_mod_id_to_crawl,
                  temp_root=None, anime_mod_id=None,org_root=None):
        """
        Copies file (currently to copy folder)
        """
        if anime_mod_id is None:
            anime_mod_id = self.anime_mod_id

        if temp_root is None and org_root is not None:
            temp_root = org_root.replace(str(anime_mod_id_to_crawl),
                                           self.out_folder + str(anime_mod_id))
        elif temp_root is None and org_root is None:
            temp_root = found_root.replace(str(anime_mod_id_to_crawl),
                                           self.out_folder + str(anime_mod_id))

        logging.info(f"Copied {found_root}{found_file} to {temp_root}{org_file}\n")
        makedirs(temp_root, exist_ok=True)
        if isfile(join(temp_root, org_file)):
            org_file2 = org_file.replace(self.file_type, suff+self.file_type)
        else:
            org_file2 = org_file
        copy(join(found_root, found_file), join(temp_root, org_file2))

    def filter_missing_files(self, anime_mod_id):
        org_mod_id = self.portrait_parser.mod_id
        file_list = self.portrait_parser.portrait_list()
        file_list = [file.replace(str(org_mod_id), str(anime_mod_id))
                                  for file in file_list]
        filtered_list = [file for file in file_list if not isfile(file)]
        # remove duplicates:
        filtered_list = list(set(filtered_list))
        return filtered_list

    def add_missing_portrait(self, file_path, anime_mod_id,
                              anime_mod_id_to_crawl,
                              criteria=contains_name, suff=''):
        root1, file1 = split(file_path)
        self.missing.write(f"{root1}{file1}\n")
        root2, file2 = self.find_alternative(root1, file1,
                                             criteria,
                                             anime_mod_id=anime_mod_id_to_crawl)
        if root2 is not None:
            self.copy_file(file1, root2, file2, suff, anime_mod_id_to_crawl,
                           anime_mod_id = anime_mod_id, org_root=root1)
            return True
        return False
            
    def add_missing_portraits(self, anime_mod_id_to_crawl,
                              criteria=contains_name, suff='',
                              anime_mod_id=None):
        if anime_mod_id is None:
            anime_mod_id = self.anime_mod_id

        filtered_list = self.filter_missing_files(anime_mod_id)

        self.write_file_list(self.parsed_out_file, filtered_list, anime_mod_id)

        missed_files = []
        for file_path in filtered_list:
            copied = self.add_missing_portrait(file_path, anime_mod_id,
                                      anime_mod_id_to_crawl,
                                      criteria=criteria, suff=suff)
            if copied is False:
                missed_files.append(file_path)
        self.write_file_list(self.diff_file, missed_files, anime_mod_id)
        
            
    @staticmethod
    def write_file_list(log_name, file_list, anime_mod_id):
        with open(log_name, 'w', encoding='utf-8') as filep:
            added_nl = [fname.replace(join(hoi4_path,f'{anime_mod_id}')+sep,'') + '\n'
                        for fname in file_list]
            role_lists = {}
            for role in ROLES:
                role_lists[role] = [fname for fname in added_nl if '/'+role+'/' in fname]
            misc = set(added_nl)
            misc = misc.difference(*[val for val in role_lists.values()])
            misc = list(misc)
            role_lists[MISC_KEY] = misc
            
            for key, val in role_lists.items():
                filep.write(f"\n{key}:\n")
                filep.writelines(val)
        
            
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

portrait_parser = PortraitParser(mod_id)
crawler = ModCrawler(mod_id, anime_mod_id)


def test_if_file_there():
    root1 = '/home/maldun/.local/share/Steam/steamapps/workshop/content/394360/820260968/gfx/interface/techtree'
    file1 = 'techtree_tank_tab.dds'
    assert crawler.check_if_file_there(root1, file1) is True

def test_if_file_there2():
    root1 = '/home/maldun/.local/share/Steam/steamapps/workshop/content/394360/820260968/gfx/leaders/MEX/'
    file1 = 'Portrait_MEX_Lazaro_Cardenas.dds'
    assert not crawler.check_if_file_there(root1, file1) is True
    
def test_lax_file_compare():
    file_name1 = "Portrait_Mexico_Lazaro_Cardenas"
    file_name2 = "Portrait_MEX_Lazaro_Cardenas"
    assert contains_name(file_name1, file_name2)

def test_find_alternative():
    root1 = '/home/maldun/.local/share/Steam/steamapps/workshop/content/394360/820260968/gfx/leaders/MEX/'
    file1 = 'Portrait_MEX_Lazaro_Cardenas.dds'
    root2, file2 = crawler.find_alternative(root1, file1, contains_name)
    assert file2 == 'Portrait_Mexico_Lazaro_Cardenas.dds'

def test_find_replacement():
    root1 = '/home/maldun/.local/share/Steam/steamapps/workshop/content/394360/820260968/gfx/leaders/MEX/'
    file1 = 'Portrait_MEX_Lazaro_Cardenas.dds'
    result = crawler.find_replacement(root1, file1, crawler.anime_mod_id,
                                            criteria=contains_name, suff='', write=True, copy=False)
    assert result is not None
    assert result[2] == 'Portrait_Mexico_Lazaro_Cardenas.dds'
    assert result[0] == file1

def test_parse_file():
    #file = f"{mod_id}/common/characters/LAT.txt"
    file = f"{mod_id}/common/characters/MAF+ characters.txt"
    var = "large"
    expr = f'{var}(\s*)=(\s*)\"(.*)\"'
    result = portrait_parser.parse_file_for_expression(file, expr)
    
    assert len(result) == 17

def test_replace_path():
    #file = f"{mod_id}/common/characters/LAT.txt"
    file = f"{mod_id}/common/characters/MAF+ characters.txt"
    var = "large"
    expr = f'{var}(\s*)=(\s*)\"(.*)\"'
    result = portrait_parser.parse_file_for_expression(file, expr)
    fname = result[0]
    result = portrait_parser.replace_path(fname, "LAT")
    assert 'gfx/leaders/LAT/Portrait_latvia_karlis_ulmanis.dds' == result

def test_replace_paths():
    file = f"{mod_id}/common/characters/LAT.txt"
    var = "large"
    expr = f'{var}(\s*)=(\s*)\"(.*)\"'
    paths = portrait_parser.parse_file_for_expression(file, expr)
    result = portrait_parser.replace_paths(paths, "LAT.txt")
    assert all([res.startswith("gfx") and res.endswith(portrait_parser.pfile_type)
                for res in result])

def test_portrait_list():
    result = portrait_parser._portrait_list()
    result2 = portrait_parser.portrait_list()
    assert len(result) == len(result2)
    assert all([r.startswith(join(hoi4_path, str(mod_id))) for r in result2])

def test_filter_missing_files():
    result = crawler.filter_missing_files(anime_mod_id)
    result2 = portrait_parser.portrait_list()
    assert len(result) < len(result2)

TEST = False
if TEST:
    # test_if_file_there()
    # test_if_file_there2()
    test_lax_file_compare()
    # test_find_alternative()
    # test_find_replacement()
    test_parse_file()
    test_replace_path()
    test_replace_paths()
    test_portrait_list()
    test_filter_missing_files()
    exit(0)

if __name__ == "__main__":
    logging.info("Crawl {}\n".format(anime_mod_id))
    for file_type in [".png", ".dds"]:
        logging.info(f"Crawl for {file_type}")
        portrait_parser = PortraitParser(mod_id, pfile_type=file_type)
        crawler = ModCrawler(mod_id, anime_mod_id, file_type=file_type)
        #crawler.crawl()
        for k, mid in enumerate(anime_mod_ids_to_crawl):
            logging.info("Lax Crawl {} Mod Nr:{}\n".format(mid, k))
            #crawler.crawl(anime_mod_id_to_crawl=mid,
            #            suff=f"_v{k}", write=False,
            #            criteria=contains_name)
            crawler.add_missing_portraits(mid)
