from PIL import Image
import gf
import numpy as np
from dataclasses import dataclass, fields, field
from typing import List
import binascii
import texture2ddecoder
import pkg_db


@dataclass
class DDSHeader:
    MagicNumber: np.uint32 = np.uint32(0)
    dwSize: np.uint32 = np.uint32(0)
    dwFlags: np.uint32 = np.uint32(0)
    dwHeight: np.uint32 = np.uint32(0)
    dwWidth: np.uint32 = np.uint32(0)
    dwPitchOrLinearSize: np.uint32 = np.uint32(0)
    dwDepth: np.uint32 = np.uint32(0)
    dwMipMapCount: np.uint32 = np.uint32(0)
    dwReserved1: List[np.uint32] = field(default_factory=list)  # size 11, [11]
    dwPFSize: np.uint32 = np.uint32(0)
    dwPFFlags: np.uint32 = np.uint32(0)
    dwPFFourCC: np.uint32 = np.uint32(0)
    dwPFRGBBitCount: np.uint32 = np.uint32(0)
    dwPFRBitMask: np.uint32 = np.uint32(0)
    dwPFGBitMask: np.uint32 = np.uint32(0)
    dwPFBBitMask: np.uint32 = np.uint32(0)
    dwPFABitMask: np.uint32 = np.uint32(0)
    dwCaps: np.uint32 = np.uint32(0)
    dwCaps2: np.uint32 = np.uint32(0)
    dwCaps3: np.uint32 = np.uint32(0)
    dwCaps4: np.uint32 = np.uint32(0)
    dwReserved2: np.uint32 = np.uint32(0)


def conv(num):
    return "".join(gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(np.uint32(num))[2:], 8), 8))


def get_uncomp_image(img_file, width, height):
    fb = open(f'I:/d1/output/{gf.get_pkg_name(img_file)}/{img_file}.bin', 'rb').read()
    img = Image.frombytes('RGB', [width, height], fb)
    img.save(f'imagetests/{img_file}.png')


def get_image(img_file, width, height, savedir):
    form = '1'

    # if DXT1 BC1 or BC4 block_size = 8 else block_size = 16
    if '1' in form or '4' in form:
        block_size = 8
    else:
        block_size = 16

    # block-compressed
    if 'DX' in form:
        pitch_or_linear_size = max(1, (width+3)/4)*block_size

        header = f'444453207C00000007100800{conv(height)}{conv(width)}{conv(pitch_or_linear_size)}000000000000000000000000000000000000000000000000000' \
                     f'000000000000000000000000000000000000000000000000000002000000005000000{conv(int(gf.get_flipped_hex("44583130", 8), 16))}0000000000000000000000' \
                     f'0000000000000000000010000000000000000000000000000000000000{conv(84)}03000000000000000100000001000000'
    # elif 'R8GB_B8G8' in form or 'G8R8_G8B8' in form:
    #     # R8G8_B8G8 or G8R8_G8B8
    #     pitch_or_linear_size = conv(((width + 1) >> 1) * 4)
    else:
        # Any other
        print('other')
        bits_per_pixel = 8  # Assuming its always 8 here which it should be as non-HDR
        pitch_or_linear_size = (width * bits_per_pixel + 8) / 8
        header = f'444453207C0000000F100000{conv(height)}{conv(width)}{conv(pitch_or_linear_size)}0000000000000000000000000000000000000000000000' \
                       '000000000000000000000000000000000000000000000000000000000020000000410000000000000020000000FF00' \
                       '000000FF00000000FF00000000FF0010000000000000000000000000000000000000'



    data = open(f'I:/d1/output/{gf.get_pkg_name(img_file)}/{img_file}.bin', 'rb').read()
    # Compressed
    bc1_header = DDSHeader()  # 0x0
    bc1_header.MagicNumber = int('20534444', 16)  # 0x4
    bc1_header.dwSize = 124  # 0x8
    bc1_header.dwFlags = (0x1 + 0x2 + 0x4 + 0x1000) + 0x80000
    bc1_header.dwHeight = height  # 0xC
    bc1_header.dwWidth = width  # 0x10
    bc1_header.dwPitchOrLinearSize = pitch_or_linear_size  # 0x14
    bc1_header.dwDepth = 0
    bc1_header.dwMipMapCount = 0
    bc1_header.dwReserved1 = [0]*11
    bc1_header.dwPFSize = 32
    bc1_header.dwPFFlags = 0x1 + 0x4  # contains alpha data + contains uncompressed RGB data
    bc1_header.dwPFFourCC = int(gf.get_flipped_hex('44585433', 8), 16)
    bc1_header.dwPFRGBBitCount = 0
    bc1_header.dwPFRBitMask = 0  # RGBA so FF first, but this is endian flipped
    bc1_header.dwPFGBitMask = 0
    bc1_header.dwPFBBitMask = 0
    bc1_header.dwPFABitMask = 0
    # bc1_header.dwCaps = 0x1000 + 0x8
    # bc1_header.dwCaps2 = 0x200 + 0x400 + 0x800 + 0x1000 + 0x2000 + 0x4000 + 0x8000  # All faces for cubemap
    bc1_header.dwCaps = 0x1000
    bc1_header.dwCaps2 = 0
    bc1_header.dwCaps3 = 0
    bc1_header.dwCaps4 = 0
    bc1_header.dwReserved2 = 0

    # if width*height != len(data):  # Compressed
    with open(savedir, 'wb') as b:
        b.write(binascii.unhexlify(header))
        b.write(data)
    # else:
    #     print('uhh')
    # else:
    #     get_uncomp_image(img_file, width, height)
    # write_file(bc1_header, header, data, f'I:/imgtests/{img_file}.dds')


def write_file(header, ogheader, file_hex, save_path):
    # DDS currently broken
    print('a')
    with open(save_path, 'wb') as b:
        for f in fields(header):
            if f.type == np.uint32:
                flipped = "".join(gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(np.uint32(getattr(header, f.name)))[2:], 8), 8))
            elif f.type == List[np.uint32]:
                flipped = ''
                for val in getattr(header, f.name):
                    flipped += "".join(
                        gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(np.uint32(val))[2:], 8), 8))
            else:
                print(f'ERROR {f.type}')
                return
            b.write(binascii.unhexlify(flipped))
        b.write(file_hex)


def get_comp_image(img_file):
    fb = open(f'I:/d1/output/{gf.get_pkg_name(img_file)}/{img_file}.bin', 'rb').read()
    dec = texture2ddecoder.decode_bc3(fb, 1024, 512)
    img = Image.frombytes('RGBA', [1024, 512], dec, 'raw', ("BGRA"))
    img.save(f'imagetests/{img_file}.png')


if __name__ == '__main__':
    # file = '012C-1145'
    file = '003B-09BF'
    # get_uncomp_image(file)
    # get_comp_image(file)
    file = '003B-09BF'
    # get_image(file, 1024, 512)

    pkg_db.start_db_connection('ps3')
    all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                                       pkg_db.get_entries_from_table('Everything',
                                                                     'FileName, Reference, FileType')}.items()}
    # img = '0233-0016'
    for header in all_file_info.keys():
        if '012C-' not in header:
            continue
        if all_file_info[header]['FileType'] == 'Texture Header':
            print(f'saved {header}.dds')
            fb = open(f'I:/d1/output/{gf.get_pkg_name(header)}/{header}.bin', 'rb').read()
            # if b'\xBE\xEF\xCA\xFE' in fb:  # Texture header
            width = gf.get_int16_big(fb, 0x20)
            height = gf.get_int16_big(fb, 0x22)
            ref_file = gf.get_file_from_hash_d2(all_file_info[header]['Reference'])
            u = gf.get_file_from_hash_d2(all_file_info[ref_file]['Reference'])
            if u != 'FBFF-1FFF':
                ref_file = u
            gf.mkdir(f'I:/d1/images/{gf.get_pkg_name(header)}')
            get_image(ref_file, width, height, f'I:/d1/images/{gf.get_pkg_name(header)}/{header}.dds')
            print(f'saved {header}.dds')