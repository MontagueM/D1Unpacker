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
    # dxgiFormat: np.uint32 = np.uint32(0)
    # resourceDimension: np.uint32 = np.uint32(0)
    # miscFlag: np.uint32 = np.uint32(0)
    # arraySize: np.uint32 = np.uint32(0)
    # miscFlags2: np.uint32 = np.uint32(0)


with open('dxgi.format') as f:
    DXGI_FORMAT = [x.strip() for x in f.readlines()]


def conv(num):
    return "".join(gf.get_flipped_hex(gf.fill_hex_with_zeros(hex(np.uint32(num))[2:], 8), 8))


def get_uncomp_image(img_file, width, height):
    fb = open(f'I:/d1/output/{gf.get_pkg_name(img_file)}/{img_file}.bin', 'rb').read()
    try:
        img = Image.frombytes('RGB', [width, height], fb)
        img.save(f'imagetests/{img_file}.png')
    except:
        print('Fix this for uncomp')


def get_image(img_file, width, height, type, othertype, savedir, header_debug, force=None):
    if force:
        for x in DXGI_FORMAT:
            if force in x:
                form = x
                break
        else:
            form = force
            formcode = '44585434'
            # raise Exception('Incorrect force')
    # elif type == 0xE1:
    #     form = 'DXGI_FORMAT_BC1_TYPELESS'
    #     form = 'DXT4'
    #     formcode = '44585434'
    # elif type == 0xE4:
    #     form = 'DXGI_FORMAT_BC3_TYPELESS'
    #     form = 'DXT1'
    #     formcode = '44585431'
    # elif type == 0x6C:
    #     form = 'DXGI_FORMAT_R8G8B8A8_TYPELESS'
    #     form = 'RGBA'
    elif othertype in [0xA5, 0x85]:
        form = 'DXGI_FORMAT_R8G8B8A8_TYPELESS'
    elif othertype in [0xA6, 0x86, 0xBF]:  # BF is a guess
        form = 'DXGI_FORMAT_BC1_TYPELESS'
        form = 'DXT1'
        formcode = '44585431'
    # elif othertype in [0xA7, 0x87]:  # This is just guessing
    #     form = 'DXGI_FORMAT_BC2_TYPELESS'
    elif othertype in [0xA8, 0x88]:
        form = 'DXGI_FORMAT_BC3_TYPELESS'
        form = 'DXT4'
        formcode = '44585434'
    # elif othertype in [0xA9, 0x89]:  # This is just guessing
    #     form = 'DXGI_FORMAT_BC4_TYPELESS'
    # elif othertype in [0xAA, 0x8A]:  # This is just guessing
    #     form = 'DXGI_FORMAT_BC5_TYPELESS'
    elif type in [12]:
        print(f'Found unknown type {type}, please fix.')
        return False
    elif othertype in [0x84]:
        print(f'Found unknown othertype {othertype}, please fix.')
        return False
    else:
        raise Exception(f'Unknown image compression {header_debug} type {type} {hex(type)} othertype {othertype} {hex(othertype)} width {width} height {height}')

    # if DXT1 BC1 or BC4 block_size = 8 else block_size = 16
    if 'BC1' in form or 'BC4' in form:
        block_size = 8
    else:
        block_size = 16

    if 'DXT1' in form or 'DXT4' in form:
        block_size = 8
    else:
        block_size = 16

    # block-compressed
    if 'BC' in form:
        pitch_or_linear_size = max(1, (width+3)/4)*block_size

        header = f'444453207C00000007100800{conv(height)}{conv(width)}{conv(pitch_or_linear_size)}000000000000000000000000000000000000000000000000000' \
                     f'000000000000000000000000000000000000000000000000000002000000005000000{conv(int(gf.get_flipped_hex("44583130", 8), 16))}0000000000000000000000' \
                     f'0000000000000000000010000000000000000000000000000000000000{conv(DXGI_FORMAT.index(form)+1)}03000000000000000100000001000000'
    # elif 'R8GB_B8G8' in form or 'G8R8_G8B8' in form:
    #     # R8G8_B8G8 or G8R8_G8B8
    #     pitch_or_linear_size = conv(((width + 1) >> 1) * 4)
    elif 'DXT' in form:
        pitch_or_linear_size = max(1, (width+3)/4)*block_size
        # pitch_or_linear_size = width * height
        header = f'444453207C00000007100800{conv(height)}{conv(width)}{conv(pitch_or_linear_size)}000000000000000000000000000000000000000000000000000' \
                     f'000000000000000000000000000000000000000000000000000002000000005000000{conv(int(gf.get_flipped_hex(formcode, 8), 16))}0000000000000000000000' \
                     f'0000000000000000000010000000000000000000000000000000000000'
    else:
        # Any other
        # print('other')
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
    # bc1_header.dwPFFourCC = int(gf.get_flipped_hex('44583130', 8), 16)  # DX10
    bc1_header.dwPFFourCC = int(gf.get_flipped_hex('44585434', 8), 16)  # DXT3
    # bc1_header.dwPFRGBBitCount = 0
    # bc1_header.dwPFRGBBitCount = 32
    # bc1_header.dwPFRBitMask = 0xFF  # RGBA so FF first, but this is endian flipped
    # bc1_header.dwPFGBitMask = 0xFF00
    # bc1_header.dwPFBBitMask = 0xFF0000
    # bc1_header.dwPFABitMask = 0xFF000000
    # bc1_header.dwCaps = 0x1000 + 0x8
    # bc1_header.dwCaps2 = 0x200 + 0x400 + 0x800 + 0x1000 + 0x2000 + 0x4000 + 0x8000  # All faces for cubemap
    bc1_header.dwCaps = 0x1000
    bc1_header.dwCaps2 = 0
    bc1_header.dwCaps3 = 0
    bc1_header.dwCaps4 = 0
    bc1_header.dwReserved2 = 0
    # bc1_header.dxgiFormat = DXGI_FORMAT.index(form)+1
    # bc1_header.resourceDimension = 3  # DDS_DIMENSION_TEXTURE2D
    # bc1_header.miscFlag = 0
    # # # int(((int(bc1_header.dwWidth) * int(bc1_header.dwHeight)) + 320) / c_data_size)
    # bc1_header.arraySize = 1
    # bc1_header.miscFlags2 = 0x0 #?

    # if width*height != len(data):  # Compressed

    # else:
    #     print('uhh')
    # if 'DXT' in form:
    with open(savedir, 'wb') as b:
        b.write(binascii.unhexlify(header))
        b.write(data)
    # else:
    #     get_uncomp_image(img_file, width, height)
    # write_file(bc1_header, header, data, f'I:/imgtests/{img_file}.dds')
    return True


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
        print(f'written to {save_path}')


def get_comp_image(img_file):
    fb = open(f'I:/d1/output/{gf.get_pkg_name(img_file)}/{img_file}.bin', 'rb').read()
    dec = texture2ddecoder.decode_bc3(fb, 1024, 512)
    img = Image.frombytes('RGBA', [1024, 512], dec, 'raw', ("BGRA"))
    img.save(f'imagetests/{img_file}.png')


if __name__ == '__main__':
    # file = '012C-1145'
    file = '01CF-058A'
    # get_uncomp_image(file, 128, 512)
    # quit()
    # get_comp_image(file)
    file = '0059-1872'
    # get_image(file, 512, 512, 'N/A', 'na', f'imagetests/{file}.dds', 'na', force='DXT4')
    # quit()
    pkg_db.start_db_connection('ps3')
    all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                                       pkg_db.get_entries_from_table('Everything',
                                                                     'FileName, Reference, FileType')}.items()}
    # img = '0233-0016'
    counter = 0
    for header in all_file_info.keys():
        # if '0077-' not in header:
        #     continue
        if all_file_info[header]['FileType'] == 'Texture Header':
            fb = open(f'I:/d1/output/{gf.get_pkg_name(header)}/{header}.bin', 'rb').read()
            if b'\xBE\xEF\xCA\xFE' in fb:  # Texture header
                width = gf.get_int16_big(fb, 0x20)
                height = gf.get_int16_big(fb, 0x22)
                type = fb[0x7]
                othertype = fb[0x0]
                ref_file = gf.get_file_from_hash_d2(all_file_info[header]['Reference'])
                u = gf.get_file_from_hash_d2(all_file_info[ref_file]['Reference'])
                if u != 'FBFF-1FFF':
                    ref_file = u
                gf.mkdir(f'I:/d1/images_dxt_counter/{gf.get_pkg_name(header)}')
                ret = get_image(ref_file, width, height, type, othertype, f'I:/d1/images_dxt_counter/{gf.get_pkg_name(header)}/{counter}.dds', header)
                if ret:
                    print(f'saved {header}.dds, img {ref_file}')
                    counter += 1