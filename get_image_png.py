from PIL import Image
import gf
import texture2ddecoder


def get_image(img_file, width, height, type, othertype, header_debug):
    if othertype in [0xA5, 0x85]:
        form = 'DXGI_FORMAT_R8G8B8A8_TYPELESS'
    elif othertype in [0xA6, 0x86, 0xBF]:  # BF is a guess
        form = 'DXGI_FORMAT_BC1_TYPELESS'
    elif othertype in [0xA8, 0x88]:
        form = 'DXGI_FORMAT_BC3_TYPELESS'
    elif type in [12]:
        print(f'Found unknown type {type}, please fix.')
        return False
    elif othertype in [0x84]:
        print(f'Found unknown othertype {othertype}, please fix.')
        return False
    else:
        raise Exception(f'Unknown image compression {header_debug} type {type} {hex(type)} othertype {othertype} {hex(othertype)} width {width} height {height}')

    fb = open(f'I:/d1/output/{gf.get_pkg_name(img_file)}/{img_file}.bin', 'rb').read()
    if 'BC1' in form:
        dec = texture2ddecoder.decode_bc1(fb, width, height)
        img = Image.frombytes('RGBA', [width, height], dec, 'raw', ("BGRA"))
    elif 'BC3' in form:
        dec = texture2ddecoder.decode_bc3(fb, width, height)
        img = Image.frombytes('RGBA', [width, height], dec, 'raw', ("BGRA"))
    elif 'R8G8B8A8' in form:
        img = Image.frombytes('RGBA', [width, height], fb)
    else:
        raise Exception(f'Invalid form type for PNG output {form}')
    # img.save(savedir)
    return img


def get_image_png(tex_header, all_file_info):
    fb = open(f'I:/d1/output/{gf.get_pkg_name(tex_header)}/{tex_header}.bin', 'rb').read()
    if b'\xBE\xEF\xCA\xFE' in fb:  # Texture header
        width = gf.get_int16_big(fb, 0x20)
        height = gf.get_int16_big(fb, 0x22)
        type = fb[0x7]
        othertype = fb[0x0]
        ref_file = gf.get_file_from_hash_d2(all_file_info[tex_header]['Reference'])
        u = gf.get_file_from_hash_d2(all_file_info[ref_file]['Reference'])
        if u != 'FBFF-1FFF':
            ref_file = u
        gf.mkdir(f'I:/d1/images_png_counter/{gf.get_pkg_name(tex_header)}')
        return get_image(ref_file, width, height, type, othertype, tex_header)
    else:
        raise Exception('File given is not a texture header')
