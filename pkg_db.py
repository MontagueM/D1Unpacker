import sqlite3 as sq
import gf

con = None
c = None


def start_db_connection(version):
    global con
    global c
    print(version)
    con = sq.connect(f'db/{version}.db')
    c = con.cursor()


def drop_table(pkg_str_to_drop):
    global c
    c.execute(f'DROP TABLE IF EXISTS {pkg_str_to_drop}')


def add_decoded_entries(decoded_entries, pkg_str):
    global con
    global c
    entries = [(int(decoded_entry.ID), decoded_entry.FileName.upper(),
                gf.get_flipped_hex(gf.get_hash_from_file(decoded_entry.FileName.upper()), 8).upper(),
                decoded_entry.Reference,
               int(decoded_entry.FileSize),
               int(decoded_entry.Type), int(decoded_entry.SubType), decoded_entry.FileType,
                "0x" + gf.fill_hex_with_zeros(hex(decoded_entry.RefID)[2:], 4).upper(),
                "0x" + gf.fill_hex_with_zeros(hex(decoded_entry.RefPackageID)[2:], 4).upper(),
                ) for decoded_entry in decoded_entries]
    c.execute(f'CREATE TABLE IF NOT EXISTS {pkg_str} (ID INTEGER, FileName TEXT, Hash TEXT, Reference TEXT, FileSizeB INTEGER, Type INTEGER, SubType INTEGER, FileType TEXT, RefID TEXT, RefPKG TEXT)')
    c.execute(f'CREATE TABLE IF NOT EXISTS Everything (FileName TEXT, Hash TEXT, Reference TEXT, FileSizeB INTEGER, Type INTEGER, SubType INTEGER, FileType TEXT, RefID TEXT, RefPKG TEXT)')
    c.executemany(f'INSERT INTO {pkg_str} (ID, FileName, Hash, Reference, FileSizeB, Type, SubType, FileType, RefID, RefPKG) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);',
              entries)
    c.executemany(f'INSERT INTO Everything (FileName, Hash, Reference, FileSizeB, Type, SubType, FileType, RefID, RefPKG) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);',
              [x[1:] for x in entries])
    con.commit()
    print(f"Added {len(decoded_entries)} decoded entries to db")


def get_entries_from_table(pkg_str, column_select='*'):
    global c
    c.execute(f"SELECT {column_select} from {pkg_str}")
    rows = c.fetchall()
    return rows


def get_all_tables():
    c.execute("select * from sqlite_master")
    table_list = c.fetchall()
    return table_list
