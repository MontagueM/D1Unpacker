from dataclasses import dataclass, fields, field
import numpy as np
from typing import List
import pkg_db
import gf
import os
from ctypes import cdll, c_char_p, create_string_buffer
import binascii
import io
from datetime import datetime

"""
Main program with every other file concatenated into a single file
"""


def get_file_typename(file_type, file_subtype, reference, file_size):
    if file_type == 8:
        if reference == 'B51A8080':
            return 'Dynamic Model Header 2'
        elif reference == '61088080':
            return 'Dynamic Model Header 1'
        elif reference == '4C1B8080':
            return 'Material'
        return '8080xxxx Structure File'
    elif file_type == 16 and file_subtype == 0:
        if file_size == 88:  # Not always the case sadly. Also need to check for BEEFCAFE
            return 'Texture Header'
        elif file_size == 12:
            return 'Index/Vertex Header'
        return 'Header'
    elif file_type == 0 and file_subtype == 4:
        return 'Model-related Data'
    elif file_type == 4 and file_subtype == 0:
        return 'RIFX Data'
    elif file_type == 32 and file_subtype == 4:
        return 'Small Texture Data'
    elif file_type == 2 and file_subtype == 4:
        return 'Large Texture Data'
    else:
        return 'Unknown'


def calculate_pkg_id(entry_a_data):
    ref_pkg_id = (entry_a_data >> 13) & 0x3FF
    ref_unk_id = entry_a_data >> 23

    ref_digits = ref_unk_id & 0x3
    if ref_digits == 1:
        return ref_pkg_id
    else:
        return ref_pkg_id | 0x100 << ref_digits


# All of these decoding functions use the information from formats.c on how to decode each entry
def decode_entry_a(entry_a_data):
    ref_id = entry_a_data & 0x1FFF
    # ref_pkg_id = (entry_a_data >> 13) & 0x3FF
    ref_pkg_id = calculate_pkg_id(entry_a_data)
    ref_unk_id = (entry_a_data >> 23) & 0x1FF

    return np.uint16(ref_id), np.uint16(ref_pkg_id), np.uint16(ref_unk_id)


def decode_entry_b(entry_b_data):
    file_subtype = (entry_b_data >> 6) & 0x7
    file_type = (entry_b_data >> 9) & 0x7F
    # print(file_type)
    return np.uint8(file_type), np.uint8(file_subtype)


def decode_entry_c(entry_c_data):
    starting_block = entry_c_data & 0x3FFF
    starting_block_offset = ((entry_c_data >> 14) & 0x3FFF) << 4
    return starting_block, starting_block_offset


def decode_entry_d(entry_c_data, entry_d_data):
    file_size = (entry_c_data & 0x3FFFFFF) << 4 | (entry_d_data >> 28) & 0xF
    unknown = (entry_d_data >> 26) & 0x3F

    return np.uint32(file_size), np.uint8(unknown)


class OodleDecompressor:
    """
    Oodle decompression implementation.
    Requires Windows and the external Oodle library.
    """

    def __init__(self, library_path: str) -> None:
        """
        Initialize instance and try to load the library.
        """
        if not os.path.exists(library_path):
            raise Exception("Could not open Oodle DLL, make sure it is configured correctly.")

        try:
            self.handle = cdll.LoadLibrary(library_path)
        except OSError as e:
            raise Exception(
                "Could not load Oodle DLL, requires Windows and 64bit python to run."
            ) from e

    def decompress(self, payload: bytes) -> bytes:
        """
        Decompress the payload using the given size.
        """
        force_size = int('0x40000', 16)
        output = create_string_buffer(force_size)
        self.handle.OodleLZ_Decompress(
            c_char_p(payload), len(payload), output, force_size,
            0, 0, 0, None, None, None, None, None, None, 3)
        return output.raw


class PkgHeader:
    def __init__(self, pbin):
        self.PackageID = gf.get_int16_big(pbin, 0x4)
        self.PackageIDH = gf.fill_hex_with_zeros(hex(self.PackageID)[2:], 4)
        self.PatchID = gf.get_int16_big(pbin, 0x20)

        self.EntryTableOffset = gf.get_int32_big(pbin, 0xB8)
        # self.EntryTableLength = get_int_hex(0x48, phex)
        # Big endian
        self.EntryTableSize = gf.get_int32_big(pbin, 0xB4)
        self.EntryTableLength = self.EntryTableSize * 0x16

        self.BlockTableSize = gf.get_int32_big(pbin, 0xD0)
        self.BlockTableOffset = gf.get_int32_big(pbin, 0xD4)


@dataclass
class SPkgEntry:
    EntryA: np.uint32 = np.uint32(0)
    EntryB: np.uint32 = np.uint32(0)
    EntryC: np.uint32 = np.uint32(0)
    EntryD: np.uint32 = np.uint32(0)
    EntryABin: bytes = b''

    '''
     [             EntryD              ] [             EntryC              ] 
     GGGGGGFF FFFFFFFF FFFFFFFF FFFFFFFF FFFFEEEE EEEEEEEE EEDDDDDD DDDDDDDD

     [             EntryB              ] [             EntryA              ]
     00000000 00000000 TTTTTTTS SS000000 CCCCCCCC CBBBBBBB BBBAAAAA AAAAAAAA

     A:RefID: EntryA & 0x1FFF
     B:RefPackageID: (EntryA >> 13) & 0x3FF
     C:RefUnkID: (EntryA >> 23) & 0x1FF
     D:StartingBlock: EntryC & 0x3FFF
     E:StartingBlockOffset: ((EntryC >> 14) & 0x3FFF) << 4
     F:FileSize: (EntryD & 0x3FFFFFF) << 4 | (EntryC >> 28) & 0xF
     ---
     new filesize maybe:
     F:FileSize: (EntryC & 0xFF) | (EntryD & 0xC0)
     maybe entryD and entryC flipped?
     
     G:Unknown: (EntryD >> 26) & 0x3F

     Flags (Entry B)
     S:SubType: (EntryB >> 6) & 0x7
     T:Type:  (EntryB >> 9) & 0x7F
    '''


@dataclass
class SPkgEntryDecoded:
    ID: np.uint16 = np.uint16(0)
    FileName: str = ''
    FileType: str = ''
    Reference: str = ''
    RefID: np.uint16 = np.uint16(0)  # uint13
    RefPackageID: np.uint16 = np.uint16(0)  # uint9
    RefUnkID: np.uint16 = np.uint16(0)  # uint10
    Type: np.uint8 = np.uint8(0)  # uint7
    SubType: np.uint8 = np.uint8(0)  # uint3
    StartingBlock: np.uint16 = np.uint16(0)  # uint14
    StartingBlockOffset: np.uint32 = np.uint32(0)  # uint14
    FileSize: np.uint32 = np.uint32(0)  # uint30
    Unknown: np.uint8 = np.uint8(0)  # uint6



@dataclass
class SPkgEntryTable:
    Entries: List[SPkgEntryDecoded] = field(default_factory=list)  # This list of of length [EntryTableSize]


@dataclass
class SPkgBlockTableEntry:
    ID: int = 0  # 0x0
    Offset: np.uint32 = np.uint32(0)  # 0x4
    Size: np.uint32 = np.uint32(0)  # 0x8
    PatchID: np.uint16 = np.uint16(0)  # 0xC
    Flags: np.uint16 = np.uint16(0)  # 0xE
    Hash: List[np.uint8] = field(default_factory=list)  # [0x14] = 20  # 0x22


@dataclass
class SPkgBlockTable:
    Entries: List[SPkgBlockTableEntry] = field(default_factory=list)  # This list of length [BlockTableSize]


class Package:
    BLOCK_SIZE = int('0x40000', 16)

    def __init__(self, package_directory):
        self.package_directory = package_directory
        if '_en_' in self.package_directory:
            self.t_package_id = self.package_directory[-13:-9]
        else:
            self.t_package_id = self.package_directory[-10:-6]
        self.package_header = None
        self.entry_table = None
        self.block_table = None
        self.all_patch_ids = []
        self.max_pkg_bin = None

    def extract_package(self, custom_direc, extract=True, largest_patch=True):
        self.get_all_patch_ids()
        if largest_patch:
            self.set_largest_patch_directory()
        print(f"Extracting files for {self.package_directory}")

        # pkg_db.start_db_connection()
        pkg_db.drop_table(self.package_directory.split(f'/{prefix}')[-1][1:-6])

        self.max_pkg_bin = open(self.package_directory, 'rb').read()
        self.package_header = self.get_header()
        self.entry_table = self.get_entry_table()
        self.block_table = self.get_block_table()

        pkg_db.add_decoded_entries(self.entry_table.Entries, self.package_directory.split(f"/{prefix}")[-1][1:-6])
        if extract:
            self.process_blocks(custom_direc)

    def get_all_patch_ids(self):
        # print(self.package_directory.split(f'/{prefix}')[0])
        all_pkgs = [x for x in os.listdir(self.package_directory.split(f'/{prefix}')[0]) if self.t_package_id in x]
        all_pkgs.sort()
        self.all_patch_ids = [int(x[-5]) for x in all_pkgs]

    def set_largest_patch_directory(self):
        if 'unp1' in self.package_directory:
            all_pkgs = [x for x in os.listdir(self.package_directory.split(f'/{prefix}')[0]) if x[:-6] in self.package_directory]
        else:
            all_pkgs = [x for x in os.listdir(self.package_directory.split(f'/{prefix}')[0]) if self.t_package_id in x]
        sorted_all_pkgs, _ = zip(*sorted(zip(all_pkgs, [int(x[-5]) for x in all_pkgs])))
        self.package_directory = self.package_directory.split(f'/{prefix}')[0] + '/' + sorted_all_pkgs[-1]
        return

    def get_header(self):
        """
        Given a pkg directory, this gets the header data and uses SPkgHeader() struct to fill out the fields of that struct,
        making a header struct with all the correct data.
        :param pkg_dir:
        :return: the pkg header struct
        """
        header_length = int('0x16F', 16)
        # The header data is 0x16F bytes long, so we need to x2 as python reads each nibble not each byte
        header = self.max_pkg_bin[:header_length]
        pkg_header = PkgHeader(header)
        return pkg_header

    def get_entry_table(self):
        """
        After we've got the header data for each pkg we know where the entry table is. Using this information, we take each
        row of 16 bytes (128 bits) as an entry and separate the row into EntryA, B, C, D for decoding
        :param pkg_data: the hex data from pkg
        :param entry_table_size: how long this entry table is in the pkg data
        :param entry_table_offset: hex offset for where the entry table starts
        :return: the entry table made
        """

        entry_table = SPkgEntryTable()
        entries_to_decode = []
        entry_table_start = self.package_header.EntryTableOffset
        entry_table_data = self.max_pkg_bin[entry_table_start:entry_table_start+self.package_header.EntryTableLength]

        for i in range(0, self.package_header.EntryTableSize * 16, 16):
            entry = SPkgEntry(gf.get_int32_big(entry_table_data, i),
                              gf.get_int32(entry_table_data, i+4),
                              gf.get_int32_big(entry_table_data, i+8),
                              gf.get_int32_big(entry_table_data, i+12),
                              entry_table_data[i:i+4])
            entries_to_decode.append(entry)

        entry_table.Entries = self.decode_entries(entries_to_decode)
        return entry_table

    def decode_entries(self, entries_to_decode):
        """
        Given the entry table (and hence EntryA, B, C, D) we can decode each of them into data about each (file? block?)
        using bitwise operators.
        :param entry_table: the entry table struct to decode
        :return: array of decoded entries as struct SPkgEntryDecoded()

        NOTE: EntryA is the class thing people were talking about. I'll add it to the pkgs.
        """
        entries = []
        count = 0
        for entry in entries_to_decode:
            # print("\n\n")
            ref_id, ref_pkg_id, ref_unk_id = decode_entry_a(entry.EntryA)
            file_type, file_subtype = decode_entry_b(entry.EntryB)
            starting_block, starting_block_offset = decode_entry_c(entry.EntryD)
            if file_type == 16 and file_subtype == 0 and ref_id == 352:
                a = 0
            file_size, unknown = decode_entry_d(entry.EntryC, entry.EntryD)
            file_name = f"{self.package_header.PackageIDH}-{gf.fill_hex_with_zeros(hex(count)[2:], 4)}"
            reference = gf.get_flipped_hex(binascii.hexlify(entry.EntryABin).decode().upper(), 8)
            file_typename = get_file_typename(file_type, file_subtype, reference, file_size)

            decoded_entry = SPkgEntryDecoded(np.uint16(count), file_name, file_typename,
                                             reference,
                                             ref_id, ref_pkg_id, ref_unk_id, file_type, file_subtype, starting_block,
                                             starting_block_offset, file_size, unknown)
            entries.append(decoded_entry)
            count += 1
        return entries

    def get_block_table(self):
        # block_table_offset = self.package_header.EntryTableOffset + (self.package_header.EntryTableSize * 16) + 32 + 96
        block_table = SPkgBlockTable()
        block_table_data = self.max_pkg_bin[self.package_header.BlockTableOffset:self.package_header.BlockTableOffset + self.package_header.BlockTableSize*32]
        reduced_bt_data = block_table_data
        for i in range(self.package_header.BlockTableSize):
            block_entry = SPkgBlockTableEntry(ID=i)
            for fd in fields(block_entry):
                if fd.type == np.uint32:
                    value = gf.get_int32_big(reduced_bt_data, 0)
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[4:]
                elif fd.type == np.uint16:
                    value = gf.get_int16_big(reduced_bt_data, 0)
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[2:]
                elif fd.type == List[np.uint8] and fd.name == 'Hash':
                    flipped = gf.get_flipped_bin(reduced_bt_data, 20)
                    value = [c for c in flipped]
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[20:]
            block_table.Entries.append(block_entry)
        return block_table

    def process_blocks(self, custom_direc):
        all_pkg_bin = []
        # We shouldn't do this
        for i in self.all_patch_ids:
            # print(i)
            bin_data = open(f'{self.package_directory[:-6]}_{i}.pkg', 'rb').read()
            all_pkg_bin.append(bin_data)

        self.output_files(all_pkg_bin, custom_direc)


    def decompress_block(self, block_bin):
        decompressor = OodleDecompressor('I:/oo2core_3_win64.dll')
        decompressed = decompressor.decompress(block_bin)
        # print("Decompressed block")
        return decompressed

    def output_files(self, all_pkg_bin, custom_direc):
        try:
            # os.mkdir(f'{version_str}/output_all/' + self.package_directory.split(f'/{prefix}')[-1][1:-6])
            os.mkdir(custom_direc + self.package_directory.split(f'/{prefix}')[-1][1:-6])
        except FileExistsError:
            pass
        except FileNotFoundError:
            raise Exception('you forgot to change name of path folder')

        # Debugging to figure out the different style
        # for block in self.block_table.Entries:
        #     # if block == 12:
        #     current_pkg_data = all_pkg_bin[self.all_patch_ids.index(block.PatchID)]
        #     block_bin = current_pkg_data[block.Offset:block.Offset + block.Size]
        #     if block.Flags & 256:
        #         print(f'Decompressing block {block.ID}')
        #         block_bin = self.decompress_block(block_bin)
        #     with open(f'{custom_direc}{self.package_directory.split(f"/{prefix}")[-1][1:-6]}/{block.ID}.bin','wb') as f:
        #         f.write(block_bin)
        # return
        for entry in self.entry_table.Entries:
            current_block_id = entry.StartingBlock
            # if entry.StartingBlock == 12:
            #     a = 0
            #     continue
            # else:
            #     u = 0
            #     continue
            block_offset = entry.StartingBlockOffset
            block_count = int(np.floor((block_offset + entry.FileSize - 1) / self.BLOCK_SIZE))
            last_block_id = current_block_id + block_count
            file_buffer = b''  # string of length entry.Size
            while current_block_id <= last_block_id:
                current_block = self.block_table.Entries[current_block_id]
                if current_block.PatchID not in self.all_patch_ids:
                    print(f"Missing PatchID {current_block.PatchID}")
                    return
                current_pkg_data = all_pkg_bin[self.all_patch_ids.index(current_block.PatchID)]
                current_block_bin = current_pkg_data[current_block.Offset:current_block.Offset + current_block.Size]
                # We only decrypt/decompress if need to
                if current_block.Flags & 256:
                    # print(f'Decompressing block {current_block.ID}')
                    current_block_bin = self.decompress_block(current_block_bin)
                if current_block_id == entry.StartingBlock:
                    file_buffer = current_block_bin[block_offset:]
                else:
                    file_buffer += current_block_bin
                current_block_id += 1
            # if entry.ID > 6000:
            #     print('')

            file = io.FileIO(f'{custom_direc}{self.package_directory.split(f"/{prefix}")[-1][1:-6]}/{entry.FileName.upper()}.bin', 'wb')
            # print(entry.FileSize)
            if entry.FileSize != 0:
                writer = io.BufferedWriter(file, buffer_size=entry.FileSize)
                writer.write(file_buffer[:entry.FileSize])
                writer.flush()
            else:
                with open(f'{custom_direc}{self.package_directory.split(f"/{prefix}")[-1][1:-6]}/{entry.FileName.upper()}.bin', 'wb') as f:
                    f.write(file_buffer[:entry.FileSize])
            # print(f"Wrote to {entry.FileName} successfully")


def unpack_all(path, custom_direc):
    all_packages = os.listdir(path)
    single_pkgs = dict()  # USE THIS TO UNPACK MOST EFFICIENTLY
    for pkg in all_packages:
        single_pkgs[pkg[:-6]] = pkg
    pkg_db.start_db_connection(version)
    pkg_db.drop_table('Everything')
    for pkg, pkg_full in single_pkgs.items():
        # if 'edz' not in pkg:
        #     continue
        # if '0104' not in pkg:
        #     continue
        pkg = Package(f'{path}/{pkg_full}')
        pkg.extract_package(extract=False, custom_direc=custom_direc)


if __name__ == '__main__':
    version = 'ps3'
    prefix = 'ps3'
    unpack_all('I:/d1/packages/', custom_direc=f'I:/d1/output/')
