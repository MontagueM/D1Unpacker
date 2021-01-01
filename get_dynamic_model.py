import pkg_db
from dataclasses import dataclass, fields
import numpy as np
import os
import re
import gf
import fbx
import pyfbx_jo as pfb
import struct
import binascii


@dataclass
class Stride12Header:
    EntrySize: np.uint32 = np.uint32(0)
    StrideLength: np.uint32 = np.uint32(0)
    BeefCafe: np.uint32 = np.uint32(0)


class File:
    def __init__(self, name=None, uid=None, pkg_name=None):
        self.name = name
        self.uid = uid
        self.pkg_name = pkg_name


class HeaderFile(File):
    def __init__(self, header=None):
        super().__init__()
        self.header = header

    def get_header(self):
        if self.header:
            print('Cannot get header as header already exists.')
            return
        else:
            if not self.name:
                self.name = gf.get_file_from_hash(self.uid)
            pkg_name = gf.get_pkg_name(self.name)
            header_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{self.name}.bin')
            return get_header(header_hex, Stride12Header())


def get_header(file_hex, header):
    # The header data is 0x16F bytes long, so we need to x2 as python reads each nibble not each byte
    for f in fields(header):
        if f.type == np.uint32:
            flipped = file_hex[:8]
            value = np.uint32(int(flipped, 16))
            setattr(header, f.name, value)
            file_hex = file_hex[8:]
        elif f.type == np.uint16:
            flipped = file_hex[:4]
            value = np.uint16(int(flipped, 16))
            setattr(header, f.name, value)
            file_hex = file_hex[4:]
    return header


test_dir = 'I:/d1/output'


# def get_referenced_file(file):
#     pkg_name = get_pkg_name(file)
#     if not pkg_name:
#         return None, None, None
#     entries_refpkg = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, RefPKG')}
#     entries_refid = {x: y for x, y in pkg_db.get_entries_from_table(pkg_name, 'FileName, RefID')}
#     ref_pkg_id = entries_refpkg[file][2:]
#     ref_pkg_name = get_pkg_name(f'{ref_pkg_id}-')
#     if not ref_pkg_name:
#         return None, None, None
#     entries_filetype = {x: y for x, y in pkg_db.get_entries_from_table(ref_pkg_name, 'FileName, FileType')}
#
#     ref_file_name = f'{ref_pkg_id}-0000' + entries_refid[file][2:]
#     return ref_pkg_name, ref_file_name, entries_filetype[ref_file_name]


def get_float16(hex_data, j, is_uv=False):
    # flt = get_signed_int(gf.get_flipped_hex(hex_data[j * 4:j * 4 + 4], 4), 16)
    flt = int.from_bytes(binascii.unhexlify(hex_data[j * 4:j * 4 + 4]), 'big', signed=True)
    if j == 1 and is_uv:
        flt *= -1
    flt = 1 + flt / (2 ** 15 - 1)
    return flt


def get_verts_data(verts_file, all_file_info, is_uv):
    """
    Stride length 48 is a dynamic and physics-enabled object.
    """
    # TODO deal with this
    pkg_name = verts_file.pkg_name
    if not pkg_name:
        return None
    ref_file = f"{all_file_info[verts_file.name]['RefPKG'][2:]}-{all_file_info[verts_file.name]['RefID'][2:]}"
    stride_header = verts_file
    if is_uv:
        print(f'uv verts file {ref_file} stride {stride_header.header.StrideLength}')
    else:
        print(f'pos verts file {ref_file} stride {stride_header.header.StrideLength}')
    ref_pkg_name = gf.get_pkg_name(ref_file)
    # ref_pkg_name, ref_file, ref_file_type = get_referenced_file(verts_file)

    stride_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')

    # print(stride_header.header.StrideLength)
    hex_data_split = [stride_hex[i:i + stride_header.header.StrideLength * 2] for i in
                      range(0, len(stride_hex), stride_header.header.StrideLength * 2)]
    # print(verts_file.name)

    if stride_header.header.StrideLength == 4:
        """
        ???
        """
        if not is_uv:
            print('Broken')
            return
        coords = get_coords_4(hex_data_split)
    elif stride_header.header.StrideLength == 8:
        """
        Pos dyn
        """
        coords = get_coords_8(hex_data_split)
    elif stride_header.header.StrideLength == 12:
        """
        Pos dyn or uvs?
        """
        coords = get_coords_12(hex_data_split, is_uv)
    elif stride_header.header.StrideLength == 16:
        """
        Other dyn UVs
        """
        coords = get_coords_16(hex_data_split)
    elif stride_header.header.StrideLength == 20:
        """
        Other dyn UVs
        """
        coords = get_coords_20(hex_data_split)
    elif stride_header.header.StrideLength == 24:
        """
        Other dyn UVs
        """
        coords = get_coords_24(hex_data_split)
    elif stride_header.header.StrideLength == 48:
        """
        Pos physcis-based prob
        """
        coords = get_coords_48(hex_data_split)
    else:
        raise Exception(f'Need to add support for stride length {stride_header.header.StrideLength}')

    return coords


def get_coords_4(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_8(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            flt = get_float16(hex_data, j, is_uv=False)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_12(hex_data_split, is_uv):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        if is_uv:
            for j in range(2):
                flt = get_float16(hex_data, j, is_uv=False)
                coord.append(flt)
        else:
            for j in range(3):
                flt = get_float16(hex_data, j, is_uv=False)
                coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_16(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords


def get_coords_20(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords

def get_coords_24(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(2):
            flt = get_float16(hex_data, j, is_uv=True)
            coord.append(flt)
        coords.append(coord)
    return coords

def get_coords_48(hex_data_split):
    coords = []
    for hex_data in hex_data_split:
        coord = []
        for j in range(3):
            flt = struct.unpack('f', bytes.fromhex(gf.get_flipped_hex(hex_data[j * 8:j * 8 + 8], 8)))[0]
            coord.append(flt)
        coords.append(coord)
    return coords


class Submesh:
    def __init__(self):
        self.pos_verts = []
        self.adjusted_pos_verts = []
        self.norm_verts = []
        self.uv_verts = []
        self.faces = []
        self.material = None
        self.textures = []
        self.diffuse = None
        self.normal = None
        self.lod_level = 0
        self.name = None
        self.type = None
        self.stride = None
        self.entry = SubmeshEntryProper


class SubmeshEntryProper:
    def __init__(self):
        self.Material = None  # x0
        self.x4 = None
        self.PrimitiveType = None  # x6, 3 indicates triangles, 5 indicates triangle strip
        self.x8 = None
        self.IndexOffset = None  # xA
        self.xC = None
        self.IndexCount = None  # xE
        self.x10 = None
        self.x14 = None
        self.x18 = None
        self.LODLevel = None  # x1C
        self.x20 = None


def trim_verts_data(verts_data, faces_data):
    all_v = []
    for face in faces_data:
        for v in face:
            all_v.append(v)
    return verts_data[min(all_v)-1:max(all_v)]


def get_submeshes(file, index, pos_verts, uv_verts, face_hex):
    # Getting the submesh table entries
    fbin = open(f'I:/d1/output/{gf.get_pkg_name(file)}/{file}.bin', 'rb').read()
    offset = [m.start() for m in re.finditer(b'\x80\x80\x1A\xEF', fbin)][index]
    if offset == -1:
        raise Exception('File contains no submeshes')
    entry_count = gf.get_int32_big(fbin, offset-4)
    entries = []
    offset += 12
    stride = 4

    for i in range(offset, offset+0x24*entry_count, 0x24):
        entry = SubmeshEntryProper()
        entry.Material = fbin[i:i+4]
        entry.PrimitiveType = gf.get_int16_big(fbin, i+0x6)
        entry.IndexOffset = gf.get_int16_big(fbin, i+0xA)
        entry.IndexCount = gf.get_int16_big(fbin, i+0xE)
        entry.LODLevel = gf.get_int16_big(fbin, i+0x1E)
        entries.append(entry)

    if len(pos_verts) > 65535:
        stride = 8


    # Making submeshes
    submeshes = []
    for i, entry in enumerate(entries):
        submesh = Submesh()
        submesh.entry = entry
        submesh.name = f'{gf.get_hash_from_file(file)}_{i}_{submesh.lod_level}'
        submesh.material = binascii.hexlify(entry.Material).decode().upper()
        submesh.type = entry.PrimitiveType
        submesh.lod_level = entry.LODLevel

        submeshes.append(submesh)

    # Removing duplicate submeshes
    # This will need changing when materials get implemented
    existing = {}
    for submesh in list(submeshes):
        if submesh.entry.IndexOffset in existing.keys():
            if submesh.lod_level >= existing[submesh.entry.IndexOffset]:
                submeshes.remove(submesh)
                continue
        faces = get_submesh_faces(submesh, face_hex, stride)
        if not faces:
            print('Issue with model')
            return
        submesh.pos_verts = trim_verts_data(pos_verts, faces)
        if uv_verts:
            submesh.uv_verts = trim_verts_data(uv_verts, faces)
        else:
            submesh.uv_verts = uv_verts
        alt = shift_faces_down(faces)
        submesh.faces = alt
        existing[submesh.entry.IndexOffset] = submesh.lod_level

    return submeshes


def scale_and_repos_pos_verts(verts_data, fbin):
    scale = struct.unpack('f', fbin[108:108 + 4])[0]
    for i in range(len(verts_data)):
        for j in range(3):
            verts_data[i][j] *= scale

    position_shift = [struct.unpack('f', fbin[96 + 4 * i:96 + 4 * (i + 1)])[0] for i in range(3)]
    for i in range(3):
        for j in range(len(verts_data)):
            verts_data[j][i] -= (scale - position_shift[i])
    return verts_data


def scale_and_repos_uv_verts(verts_data, fbin):
    # return verts_data
    scales = [struct.unpack('f', fbin[112+i*4:112+(i+1)*4])[0] for i in range(2)]
    position_shifts = [struct.unpack('f', fbin[120+i*4:120+(i+1)*4])[0] for i in range(2)]
    for i in range(len(verts_data)):
        verts_data[i][0] *= scales[0]
        verts_data[i][1] *= -scales[1]

    for j in range(len(verts_data)):
        verts_data[j][0] -= (scales[0] - position_shifts[0])
        verts_data[j][1] += (scales[1] - position_shifts[1] + 1)
    return verts_data


def export_fbx(submeshes, model_file, name, temp_direc):
    model = pfb.Model()
    fbin = open(f'I:/d1/output/{gf.get_pkg_name(model_file)}/{model_file}.bin', 'rb').read()
    for submesh in submeshes:
        mesh = create_mesh(model, submesh, name)
        if not mesh.GetLayer(0):
            mesh.CreateLayer()
        layer = mesh.GetLayer(0)
        # if shaders:
        #     apply_shader(d2map, submesh, node)
        # apply_diffuse(d2map, submesh, node)
        if submesh.uv_verts:
            create_uv(mesh, model_file, submesh, layer)
        node = fbx.FbxNode.Create(model.scene, submesh.name)
        node.SetNodeAttribute(mesh)
        node.LclScaling.Set(fbx.FbxDouble3(100, 100, 100))
        node.SetShadingMode(fbx.FbxNode.eTextureShading)
        model.scene.GetRootNode().AddChild(node)


    if temp_direc or temp_direc != '':
        try:
            os.mkdir(f'I:/d1/dynamic_models/{temp_direc}/')
        except:
            pass
    try:
        os.mkdir(f'I:/d1/dynamic_models/{temp_direc}/{model_file}')
    except:
        pass
    model.export(save_path=f'I:/d1/dynamic_models/{temp_direc}/{model_file}/{name}.fbx', ascii_format=False)
    print(f'Written I:/d1/dynamic_models/{temp_direc}/{model_file}/{name}.fbx.')


def get_submesh_faces(submesh: Submesh, faces_hex, stride):
    # if submesh.name == '80bc5114_1_0':
    #     a = 0
    # 3 is triangles, 5 is triangle strip
    increment = 3
    start = submesh.entry.IndexOffset
    count = submesh.entry.IndexCount
    if stride == 8:
        int_faces_data = [int(faces_hex[i:i + 8], 16) + 1 for i in
                           range(0, len(faces_hex), 8)]
    else:
        int_faces_data = [int(faces_hex[i:i + 4], 16) + 1 for i in
                           range(0, len(faces_hex), 4)]
    if submesh.type == 5:
        increment = 1
        count -= 0

    faces = []
    j = 0
    for i in range(0, count, increment):
        face_index = start + i

        if 65536 in int_faces_data[face_index:face_index+3] or 4294967296 in int_faces_data[face_index:face_index+3]:
            j = 0
            continue

        if submesh.type == 3 or j % 2 == 0:
            face = int_faces_data[face_index:face_index+3]
        else:
            # face = int_faces_data[face_index:face_index+3][::-1]
            try:
                face = [int_faces_data[face_index+1], int_faces_data[face_index+0], int_faces_data[face_index+2]]
            except IndexError:
                return False  # Idk why it causes IndexError, prob wrong strip? maybe its fan? idk
        if face == []:
            a = 0
        faces.append(face)
        if len(faces) == int(count/3):
            break
        j += 1
    return faces


def get_face_hex(faces_file, all_file_info) -> str:
    try:
        ref_file = f"{all_file_info[faces_file.name]['RefPKG'][2:]}-{all_file_info[faces_file.name]['RefID'][2:]}"
    except KeyError:
        return ''
    print(f'faces file {ref_file}')
    ref_pkg_name = gf.get_pkg_name(ref_file)
    faces_hex = gf.get_hex_data(f'{test_dir}/{ref_pkg_name}/{ref_file}.bin')
    return faces_hex
    return ''



def get_verts_faces_files(model_file):
    pos_verts_files = []
    uv_verts_files = []
    faces_files = []
    pkg_name = gf.get_pkg_name(model_file)
    try:
        model_data_hex = gf.get_hex_data(f'{test_dir}/{pkg_name}/{model_file}.bin')
    except FileNotFoundError:
        print(f'No folder found for file {model_file}. Likely need to unpack it or design versioning system.')
        return None, None, None
    # Always at 0x80, 0x110, 0x1A0, ...
    num = gf.get_int32_big(bytes.fromhex(model_data_hex), 0x40)
    for i in range(num):
        rel_hex = model_data_hex[0x80*2+0x90*2*i:0x80*2+0x90*2*(i+1)]
        for j in range(0, len(rel_hex), 8):
            hsh = rel_hex[j:j+8]
            if hsh.upper() != 'FFFFFFFF':
                hf = HeaderFile()
                hf.uid = hsh
                hf.name = gf.get_file_from_hash(hf.uid)
                hf.pkg_name = gf.get_pkg_name(hf.name)
                if j == 0:
                    hf.header = hf.get_header()
                    # hf.StrideLength = 8
                    # print(f'Position file {hf.name} stride {hf.header.StrideLength}')
                    pos_verts_files.append(hf)
                elif j == 8:
                    hf.header = hf.get_header()
                    # hf.StrideLength = 20
                    # print(f'UV file {hf.name} stride {hf.header.StrideLength}')
                    uv_verts_files.append(hf)
                elif j == 32:
                    faces_files.append(hf)
                    break
    # print(pos_verts_files, uv_verts_files)
    return pos_verts_files, uv_verts_files, faces_files


def shift_faces_down(faces_data):
    a_min = faces_data[0][0]
    for f in faces_data:
        for i in f:
            if i < a_min:
                a_min = i
    for i, f in enumerate(faces_data):
        for j, x in enumerate(f):
            faces_data[i][j] -= a_min - 1
    return faces_data


def adjust_faces_data(faces_data, max_vert_used):
    new_faces_data = []
    all_v = []
    for face in faces_data:
        for v in face:
            all_v.append(v)
    starting_face_number = min(all_v) -1
    all_v = []
    for face in faces_data:
        new_face = []
        for v in face:
            new_face.append(v - starting_face_number + max_vert_used)
            all_v.append(v - starting_face_number + max_vert_used)
        new_faces_data.append(new_face)
    return new_faces_data, max(all_v)


def get_model(model_file, all_file_info, lod, temp_direc=''):
    pos_verts_files, uv_verts_files, faces_files = get_verts_faces_files(model_file)
    # fbin = open(f'I:/d1/output/{gf.get_pkg_name(model_file)}/{model_file}.bin', 'rb').read()
    # uv_verts_files = []
    for i, pos_vert_file in enumerate(pos_verts_files):
        faces_file = faces_files[i]
        pos_verts = get_verts_data(pos_vert_file, all_file_info, is_uv=False)
        # pos_verts = scale_and_repos_pos_verts(pos_verts, fbin)
        if i < len(uv_verts_files):
            uv_verts = get_verts_data(uv_verts_files[i], all_file_info, is_uv=True)
            # uv_verts = scale_and_repos_uv_verts(uv_verts, fbin)
        else:
            uv_verts = []
        # scaled_pos_verts = scale_verts(coords, model_file)
        face_hex = get_face_hex(faces_file, all_file_info)
        submeshes = get_submeshes(model_file, i, pos_verts, uv_verts, face_hex)
        if not submeshes:
            return
        first_mat = None
        submeshes_to_write = []
        for submesh in submeshes:
            # break
            if not first_mat:
                first_mat = submesh.material
            # if first_mat != submesh.material:
            #     break
            if any([x.lod_level == 0 for x in submeshes]):
                if submesh.lod_level == 0:
                    submeshes_to_write.append(submesh)
                    # write_submesh_fbx(submesh, temp_direc, model_file)
            else:
                submeshes_to_write.append(submesh)
        if lod:
            export_fbx(submeshes_to_write, model_file, pos_vert_file.uid, temp_direc)
        else:
            export_fbx(submeshes, model_file, pos_vert_file.uid, temp_direc)



def create_mesh(model, submesh: Submesh, name):
    mesh = fbx.FbxMesh.Create(model.scene, name)
    controlpoints = [fbx.FbxVector4(-x[0], x[2], x[1]) for x in submesh.pos_verts]
    for i, p in enumerate(controlpoints):
        mesh.SetControlPointAt(p, i)
    for face in submesh.faces:
        mesh.BeginPolygon()
        mesh.AddPolygon(face[0]-1)
        mesh.AddPolygon(face[1]-1)
        mesh.AddPolygon(face[2]-1)
        mesh.EndPolygon()

    # node = fbx.FbxNode.Create(d2map.fbx_model.scene, name)
    # node.SetNodeAttribute(mesh)

    return mesh


def create_uv(mesh, name, submesh: Submesh, layer):
    uvDiffuseLayerElement = fbx.FbxLayerElementUV.Create(mesh, f'diffuseUV {name}')
    uvDiffuseLayerElement.SetMappingMode(fbx.FbxLayerElement.eByControlPoint)
    uvDiffuseLayerElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)
    # mesh.InitTextureUV()
    for i, p in enumerate(submesh.uv_verts):
        uvDiffuseLayerElement.GetDirectArray().Add(fbx.FbxVector2(p[0], p[1]))
    layer.SetUVs(uvDiffuseLayerElement, fbx.FbxLayerElement.eTextureDiffuse)
    return layer


if __name__ == '__main__':
    pkg_db.start_db_connection('ps3')
    all_file_info = {x[0]: dict(zip(['RefID', 'RefPKG', 'FileType'], x[1:])) for x in
                     pkg_db.get_entries_from_table('Everything', 'FileName, RefID, RefPKG, FileType')}
    parent_file = '00FE-14F6'
    get_model(parent_file, all_file_info, lod=True)
    quit()

    for file in all_file_info:
        if 'Dynamic' in all_file_info[file]['FileType']:
            if '00FE-' not in file:
                continue
            gf.mkdir(f'I:/d1/dynamic_models/{gf.get_pkg_name(file)}/')
            get_model(file, all_file_info, lod=True, temp_direc=f'{gf.get_pkg_name(file)}/')