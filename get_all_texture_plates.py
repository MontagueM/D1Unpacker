import get_texture_plates as gtp
import pkg_db
import gf

pkg_db.start_db_connection('ps3')
all_file_info = {x: y for x, y in {x[0]: dict(zip(['Reference', 'FileType'], x[1:])) for x in
                                   pkg_db.get_entries_from_table('Everything',
                                                                 'FileName, Reference, FileType')}.items()}
# img = '0233-0016'
counter = 0
for file in all_file_info.keys():
    if 'gear' not in gf.get_pkg_name(file):
        continue
    if all_file_info[file]['FileType'] == 'Dynamic Model Header 1':
        print(file)
        texplateset = gtp.TexturePlateSet(file)
        if not texplateset.plates:  # No tex plate
            print('No texture plate')
            continue
        ret = texplateset.get_plate_set(all_file_info)
        if not ret:  # Is a tex plate but just nothing in it
            print('Nothing in texture plate')
            continue
        gf.mkdir(f'I:/d1/image_plates_png/{gf.get_pkg_name(file)}/')
        texplateset.export_texture_plate_set(f'I:/d1/image_plates_png/{gf.get_pkg_name(file)}/{counter}')
        counter += 1
