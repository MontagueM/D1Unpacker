import gf
import pkg_db
import struct
import binascii

def get_float16(hex_data, j, is_uv=False):
    # flt = get_signed_int(gf.get_flipped_hex(hex_data[j * 4:j * 4 + 4], 4), 16)
    flt = int.from_bytes(binascii.unhexlify(hex_data[j * 4:j * 4 + 4]), 'little', signed=True)
    if j == 1 and is_uv:
        flt *= -1
    flt = 1 + flt / (2 ** 15 - 1)
    return flt

def get_verts_data(verts_file, stride, float16, offset=0):
    """
    Stride length 48 is a dynamic and physics-enabled object.
    """
    # TODO deal with this
    pkg_name = gf.get_pkg_name(verts_file)
    if not pkg_name:
        return None
    verts_hex = gf.get_hex_data(f'I:/d1/output/{gf.get_pkg_name(verts_file)}/{verts_file}.bin')

    # print(stride_header.StrideLength)
    hex_data_split = [verts_hex[i:i + stride * 2] for i in
                      range(offset, len(verts_hex), stride * 2)]

    print(verts_file)
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(0, 3):
            if float16:
                flt = get_float16(hex_data, j)
            else:
                flt = struct.unpack('f', bytes.fromhex(gf.get_flipped_hex(hex_data[j*8:j*8+8], 8)))[0]
            coord.append(flt)
        # coord[-1] = 0
        coords.append(coord)

    return coords


def get_faces_data(faces_file):
    faces = []
    faces_hex = gf.get_hex_data(f'I:/d1/output/{gf.get_pkg_name(verts_file)}/{faces_file}.bin')
    int_faces_data = [int(faces_hex[i:i+4], 16)+1 for i in range(0, len(faces_hex), 4)]
    for i in range(0, len(int_faces_data), 3):
        face = []
        for j in range(3):
            face.append(int_faces_data[i+j])
        faces.append(face)
    return faces



def write_obj(verts_file, coords, faces=None):
    with open(f'test_verts/test.obj', 'w') as f:
        f.write(f'o {verts_file}\n')
        for coord in coords:
            f.write(f'v {coord[0]} {coord[1]} {coord[2]}\n')
        if faces:
            for face in faces:
                f.write(f'f {face[0]} {face[1]} {face[2]}\n')
    print(f'Written to file.')


if __name__ == '__main__':
    pkg_db.start_db_connection('ps3')
    verts_file = '00FE-14FD'
    faces = []
    # faces_file = '02BA-0AF7'
    coords = get_verts_data(verts_file, stride=12, float16=True, offset=0)
    # faces = get_faces_data(faces_file)
    write_obj(verts_file, coords, faces)
