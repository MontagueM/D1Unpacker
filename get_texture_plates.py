import gf
import binascii
import get_image_png as gip
import pkg_db
from PIL import Image, ImageOps


class TexturePlateSet:
    def __init__(self, dyn_model_1):
        self.topfile = dyn_model_1
        self.plates = self.get_plates()

    def get_plate_set(self, all_file_info):
        for type, plate in self.plates.items():
            ret = plate.get_plate_data()
            if not ret:
                return False
            plate.get_plate_textures(all_file_info)
        return True

    def get_plates(self):
        fb = open(f'I:/d1/output/{gf.get_pkg_name(self.topfile)}/{self.topfile}.bin', 'rb').read()
        # This offset is a guess for now
        offset = fb.find(b'\x80\x80\x1B\x79\xFF\xFF\xFF\xF4')+16
        platesetfile = gf.get_file_from_hash(binascii.hexlify(fb[offset:offset+4]))
        try:
            fb = open(f'I:/d1/output/{gf.get_pkg_name(platesetfile)}/{platesetfile}.bin', 'rb').read()
        except FileNotFoundError:
            return False
        diffuse = TexturePlate(gf.get_file_from_hash(binascii.hexlify(fb[0x20:0x20+4])), 'diffuse')
        normal = TexturePlate(gf.get_file_from_hash(binascii.hexlify(fb[0x24:0x24+4])), 'normal')
        gstack = TexturePlate(gf.get_file_from_hash(binascii.hexlify(fb[0x28:0x28+4])), 'gstack')
        return {'diffuse': diffuse, 'normal': normal, 'gstack': gstack}

    def export_texture_plate_set(self, save_dir):
        # We'll append _diffuse.png, _normal.png, _gstack.png to the save_dir per set
        for type, plate in self.plates.items():
            plate.export_plate(f'{save_dir}_{type}.png')


class TexturePlate:
    def __init__(self, platefile, type):
        self.file = platefile
        self.type = type
        self.textures = []

    def get_plate_data(self):
        if self.file == 'FBFF-1FFF':
            return False
        fb = open(f'I:/d1/output/{gf.get_pkg_name(self.file)}/{self.file}.bin', 'rb').read()
        file_count = gf.get_int16_big(fb, 0xE)
        table_offset = 0x30
        for i in range(table_offset, table_offset+file_count*20, 20):
            tex = Texture()
            tex.tex_header = gf.get_file_from_hash(binascii.hexlify(fb[i:i+4]))
            tex.platex = gf.get_int32_big(fb, i+0x4)
            tex.platey = gf.get_int32_big(fb, i+0x8)
            tex.resizex = gf.get_int32_big(fb, i+0xC)
            tex.resizey = gf.get_int32_big(fb, i+0x10)
            self.textures.append(tex)
        return True

    def get_plate_textures(self, all_file_info):
        for tex in self.textures:
            tex.image = gip.get_image_png(tex.tex_header, all_file_info)

            # Adjusting normal colours
            if self.type == 'normal':
                r, g, b, a = tex.image.split()
                # Technically we should do a green invert but to match the stuff that comes from the tool we wont do it
                # g = ImageOps.invert(g)
                b = ImageOps.invert(b)
                tex.image = Image.merge('RGB', (a, g, b))

            # Resizing
            if self.type == 'normal':
                # print(f'resizing to {tex.resizex} {tex.resizey}')
                tex.resizex *= 2
                tex.platex *= 2
            tex.image = tex.image.resize([tex.resizex, tex.resizey])

    def export_plate(self, save_dir):
        bg_plate = Image.new('RGBA', [1024, 1024], (0, 0, 0, 0))  # Makes a transparent image as alpha = 0
        for tex in self.textures:
            bg_plate.paste(tex.image, [tex.platex, tex.platey])
        bg_plate.save(save_dir)

class Texture:
    def __init__(self):
        self.tex_header = ''
        self.image = None
        self.platex = 0
        self.platey = 0
        self.resizex = 0
        self.resizey = 0


if __name__ == '__main__':
    pkg_db.start_db_connection('ps3')
    all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                                       pkg_db.get_entries_from_table('Everything',
                                                                     'FileName, Reference, FileType')}.items()}

    file = '0103-1324'
    texplateset = TexturePlateSet(file)
    ret = texplateset.get_plate_set(all_file_info)
    if not ret:
        raise Exception('Something wrong')
    texplateset.export_texture_plate_set('imagetests/test')