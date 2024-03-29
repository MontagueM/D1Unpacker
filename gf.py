import os
import numpy as np


def fill_hex_with_zeros(s, desired_length):
    return ("0"*desired_length + s)[-desired_length:]


def get_hex_data(direc):
    t = open(direc, 'rb')
    h = t.read().hex()
    return h


def get_flipped_hex(h, length):
    if length % 2 != 0:
        print("Flipped hex length is not even.")
        return None
    return "".join(reversed([h[:length][i:i + 2] for i in range(0, length, 2)]))


def get_flipped_bin(h, length):
    if length % 2 != 0:
        print("Flipped bin length is not even.")
        return None
    return h[:length][::-1]


def get_file_from_hash(hsh):
    # hsh = get_flipped_hex(hsh, 8)
    first_int = int(hsh.upper(), 16)
    one = first_int - 2155872256
    first_hex = hex(int(np.floor(one/8192)))
    second_hex = hex(first_int % 8192)
    return f'{fill_hex_with_zeros(first_hex[2:], 4)}-{fill_hex_with_zeros(second_hex[2:], 4)}'.upper()

def get_file_from_hash_d2(hsh):
    hsh = get_flipped_hex(hsh, 8)
    first_int = int(hsh.upper(), 16)
    one = first_int - 2155872256
    first_hex = hex(int(np.floor(one/8192)))
    second_hex = hex(first_int % 8192)
    return f'{fill_hex_with_zeros(first_hex[2:], 4)}-{fill_hex_with_zeros(second_hex[2:], 4)}'.upper()


def get_hash_from_file(file):
    pkg = file.replace(".bin", "").upper()

    firsthex_int = int(pkg[:4], 16)
    secondhex_int = int(pkg[5:], 16)

    one = firsthex_int*8192
    two = hex(one + secondhex_int + 2155872256)
    return two[2:]


def get_pkg_name(file):
    if not file:
        print(f'{file} is invalid.')
        return None
    pkg_id = file.split('-')[0]
    for folder in os.listdir('I:/d1/output/'):
        if pkg_id.lower() in folder.lower():
            pkg_name = folder
            break
    else:
        if '0042-' in file:
            return 'ui_startup_unpatchable'

        print(f'Could not find folder for {file}. File is likely not a model or folder does not exist.')
        return None
    return pkg_name


def mkdir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass


class File:
    def __init__(self, name=None, uid=None, pkg_name=None):
        self.name = name
        self.uid = uid
        self.pkg_name = pkg_name
        self.fhex = None

    def get_file_from_uid(self):
        self.name = get_file_from_hash(self.uid)
        return self.pkg_name

    def get_uid_from_file(self):
        self.uid = get_hash_from_file(self.name)
        return self.pkg_name

    # def get_pkg_name(self):
    #     self.pkg_name = get_pkg_name(self.name)
    #     return self.pkg_name

    # def get_hex_data(self):
    #     if not self.pkg_name:
    #         self.get_pkg_name()
    #     if not self.name:
    #         self.get_file_from_uid()
    #     self.fhex = get_hex_data(f'I:/d2_output_3_0_0_3/{self.pkg_name}/{self.name}.bin')
    #     return self.fhex


def get_int32(hx, offset):
    return int.from_bytes(hx[offset:offset+4], byteorder='little')


def get_int16(hx, offset):
    return int.from_bytes(hx[offset:offset+2], byteorder='little')


def get_int32_big(hx, offset):
    return int.from_bytes(hx[offset:offset+4], byteorder='big')


def get_int16_big(hx, offset):
    return int.from_bytes(hx[offset:offset+2], byteorder='big')
