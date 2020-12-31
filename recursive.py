import gf
import pkg_db


def search_recursive(file, search, max_depth, start_offset, string=None, ftype=None, restrict_type=False, text_16=True):
    if start_offset % 2 != 0:
        print('Start offset must be even.')
        return
    if search == 'text':
        raise Exception('Disabled')
    elif search == 'string':
        raise Exception('Disabled')
    elif search == 'type':
        if restrict_type:
            entries = {x: y for x, y in {x[0]: dict(zip(['FileName', 'Reference', 'FileType'], x[1:])) for x in
                                               pkg_db.get_entries_from_table('Everything',
                                                                             'Hash, FileName, Reference, FileType')}.items()
                             if y['FileType'] == restrict_type}
        else:
            entries = {x: y for x, y in {x[0]: dict(zip(['FileName', 'Reference', 'FileType'], x[1:])) for x in
                                               pkg_db.get_entries_from_table('Everything',
                                                                             'Hash, FileName, Reference, FileType')}.items()
                            }
        type_recursive(file, start_offset, string, max_depth, [], 0, [gf.get_flipped_hex(gf.get_hash_from_file(file), 8).upper()], entries, ftype)


def type_recursive(file, start_offset, string, max_depth, path, layer, files_searched, entries, ftype):
    pkg = gf.get_pkg_name(file)
    file_hex = gf.get_hex_data(f'I:/d1/output/{pkg}/{file}.bin').upper()

    # Checking whats in the reference
    hsh = gf.get_flipped_hex(gf.get_hash_from_file(file), 8).upper()
    if max_depth != layer:
        if entries[hsh]['Reference'] in entries.keys():
            hsh = entries[hsh]['Reference']
            if hsh not in files_searched:
                files_searched += [hsh]
                print(f'In {entries[hsh]["FileName"]} {hsh} layer {layer} type {entries[hsh]["FileType"]} ref {entries[hsh]["Reference"]} via reference')
                type_recursive(entries[hsh]["FileName"], start_offset, string, max_depth,
                               path + ['->', entries[hsh]["FileName"]], layer + 1, files_searched, entries, ftype)


    for i in range(start_offset, len(file_hex), 8):
        hsh = gf.get_flipped_hex(file_hex[i:i + 8], 8)
        if hsh == '00000000' or hsh == 'FFFFFFFF':
            continue
        if max_depth != layer:
            if hsh in entries.keys():
                if hsh not in files_searched:
                    if ftype:
                        print(f'In {entries[hsh]["FileName"]} {hsh} layer {layer}')
                    else:
                        print(f'In {entries[hsh]["FileName"]} {hsh} layer {layer} type {entries[hsh]["FileType"]} ref {entries[hsh]["Reference"]}')
                    files_searched += [hsh]
                    if ftype:
                        if entries[hsh]["FileType"][0] == ftype:
                            print(f'Found type {ftype} file is {" ".join(path) + " -> " + entries[hsh]["FileName"]} {hsh}')
                            continue
                    type_recursive(entries[hsh]["FileName"], start_offset, string, max_depth, path + ['->', entries[hsh]["FileName"]], layer+1, files_searched, entries, ftype)

    print(f'End of {file}')


if __name__ == '__main__':
    pkg_db.start_db_connection('ps3')
    search_recursive(file='0137-01C5', search='type', max_depth=8, start_offset=0)
