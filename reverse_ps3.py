import os
import re
import pkg_db
import numpy as np
import gf

search_dir = 'I:/d1/output/'
# search_dir = 'D:/D2_Datamining/Package Unpacker/2_9_0_1/output_all/'
# search_dir = 'C:/d2_output/'
# search_str = '44C9AC81'
# search_str = '4613C280'
# search_str = 'BE453381'
# search_str = 'F1C0AC81'
# search_str = '613FEC80'
# search_string = '5883C680'


banned = [#'tangled',
    # 'video',
    # 'sandbox',
    # 'cinematics',
    # 'environments',
#           'raids',
#           'combatants',
#           'audio',
#           'prison',
#           'luna',
#           'planet_x',
#           'gambit',
#           'edz',
#           'europa',
#           'dreaming',
#           'crucible',
#           'cosmo',
#           'unp1',
          ]


def find_str_binary(search_str, do_print=True, select=None, to_ban=False):
    # if ' ' in search_str:
    #     search_str = search_str.replace(' ', '')
    if do_print:
        print(f'Searching string {search_str}')
    pkg_db.start_db_connection('ps3')
    files = []
    # [::-1]
    for i, folder in enumerate(os.listdir(search_dir)):
        if to_ban:
            ban = False
            for b in banned:
                if b in folder:
                    ban = True
            if ban:
                continue
        if select not in folder:
            continue
        # if i < 17:
        #     continue
        # if 'activities' in folder:
        #     if len(folder) != 15:
        #         continue
        # else:
        #     continue
        # else:
        #     if 'investment' in folder:
        #         continue
        if '_en' in folder and 'sr' not in folder:
            continue
        # if i < 140:
        #     continue
        if do_print:
            print(f'Searching in {folder}, index {i}')
        pkg_name = gf.get_pkg_name(f'{folder.split("_")[-1]}-0000')
        all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType', 'FileSize'], x[1:])) for x in
                                           pkg_db.get_entries_from_table('Everything',
                                                                         'FileName, Reference, FileType, FileSizeB')}.items()}
        for file in os.listdir(search_dir + folder):
            fbin = open(search_dir + folder + '/' + file, 'rb').read()
            find = [m.start() for m in re.finditer(re.escape(search_str), fbin)]
            # find = file_hex.find(search_str)
            if find and find != -1:
                files.append(file)
                if do_print:
                    try:
                        hsh = gf.get_flipped_hex(gf.get_hash_from_file(file), 8).upper()
                        a = [r'\x' + hsh[i:i+2] for i in range(0, len(hsh), 2)]
                        xhsh = ''.join(a)
                        xhshd1 = ''.join(gf.get_flipped_bin(a, 4))
                        print(f'Found string in {file}, {hsh} {gf.get_flipped_hex(hsh, 8)} {xhsh} {xhshd1} "{all_file_info[file.replace(".bin", "")]["FileType"]}" FileSize {all_file_info[file.replace(".bin", "")]["FileSize"]} Ref 0x{all_file_info[file.replace(".bin", "")]["Reference"]} at bytes {find}.')  # There may be more as not accounting for copies.
                    except KeyError:
                        print('Error in printing, file not available')

    if do_print:
        print(files)
    return files


if __name__ == '__main__':
    # Speaker
    # find_str_binary(b'\x80\x87\x63\xF9', select='_')
    # find_str_binary(b'\x80\xC3\xEF\x65', select='trv')

    # Lightmail from API

    # Other armour 988AA080 \x80\xA0\x8A\x98  -> \x80\xA0\x51\xE8  A48AA080 -> \x80\xA0\x51\xE7

    # 83B581B2
    find_str_binary(b'\x80\xA0\x60\xB9', select='gear')
    # find_str_binary(b'\x10\xA3\xE8\xF2\xE9\x63\x00\x01', select='0114')

