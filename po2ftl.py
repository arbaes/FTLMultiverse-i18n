import os
import sys
import argparse

import polib
from lxml import etree

MV_DATA_PATH = 'data_src/'
MV_VERSION = "5.0"

parser = argparse.ArgumentParser(description='Generate FTL Translated files')
parser.add_argument('-i', action='store', type=str, metavar='PATH', help='Path to the directory with translated PO files.', default="po/")
parser.add_argument('-o', action='store', type=str, metavar='PATH', help='Path to the Output directory.', default="translated/")
args = parser.parse_args()

if not os.path.isdir(args.i):
    print(f'{args.i} is not a valid directory')
    sys.exit()

for fname in os.listdir(args.i):
    if fname.endswith('.po'):
        src_fname = os.path.splitext(fname)[0]
        po = None

        print(f"{fname} -> ", end="")
        try:
            po = polib.pofile(f"{args.i}{fname}")
        except IOError as e:
            print("Failed !")
            print(e)
            continue

        lang = po.metadata['Language']

        expected_src_file = f"{FTL_DATA_PATH}{src_fname}"
        if not os.path.exists(expected_src_file):
            print("Failed !")
            print(f"{src_fname} not found in reference folder {FTL_DATA_PATH} ! Skipping")
            continue

        ftl_root = etree.parse(expected_src_file)

        if not os.path.isdir(f"{args.o}"):
            os.mkdir(f"{args.o}")
        out_path = os.path.join(f"{args.o}", f"{lang}/")
        if not os.path.isdir(f"{out_path}"):
            os.mkdir(out_path)

        for entry in po:
            key = entry.msgctxt

            if not key:
                continue

            # Recover Element Identification data
            tag, name_val, rel_xpath = key.split('__')
            targets = ftl_root.findall(f'//{tag}[@name="{name_val}"]{rel_xpath}')
            for t in targets:
                t.text = entry.msgstr

        print(f'{out_path}{src_fname}')
        ftl_root.write(f'{out_path}{src_fname}', pretty_print=True, encoding='utf-8')
