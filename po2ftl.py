import os
import sys
import argparse
import shutil

import polib
from lxml import etree
import gdown
from tqdm import tqdm

TEMP_TL_DIR = 'translated'
PO_EXTRACT_DIR = 'weblate_po'
SRC_FTL_MV_DIR = 'src'

parser = argparse.ArgumentParser(description='Generate FTL Translated files')
parser.add_argument('--src', action='store', type=str, metavar='PATH', help='Path to the directory with FTL:MV Source files.')
parser.add_argument('--weblate-zip', action='store', type=str, metavar='PATH', help='Path to a Weblate .zip file.')
parser.add_argument('--po-dir', action='store', type=str, metavar='PATH', help='Path to the directory with translated PO files.')
parser.add_argument('-o', action='store', type=str, metavar='PATH', help='Path to the Output directory.', default="mods")
parser.add_argument('--debug', action='store_true', help='Verbose execution')
parser.add_argument('--dl', action='store_true', help='Download latest FTL: Multiverse as --src')
args = parser.parse_args()


# Helper to get all PO files in a directory
def get_po_list(path):
    po_files = []
    for (root, dirs, files) in os.walk(path):
        for f in files:
            if f.endswith('.po'):
                po_files.append(os.path.join(root, f))
    return po_files


print("FTL: Multiverse Translated Mods Generator")
print("==============================================")
# Validity Checks
po_files = None
if not args.weblate_zip:
    if not args.po_dir:
        print('Pleace provide PO files using --weblate-zip or --po-dir')
        sys.exit()
    if not os.path.isdir(args.po_dir):
        print(f'{args.po_dir} is not a valid directory')
        sys.exit()
    else:
        po_files = get_po_list(args.po_dir)
else:
    try:
        shutil.unpack_archive(f'{args.weblate_zip}', f'{PO_EXTRACT_DIR}/', 'zip')
    except BaseException as e:
        print(f'{args.weblate_zip} is seemingly corrupted, aborting...')
        print(e)
        sys.exit()

    po_files = get_po_list(f'{PO_EXTRACT_DIR}/')

if po_files:
    print(f'{len(po_files)} translatable .po files found !')
else:
    print('No po files found. Aborting...')
    sys.exit()

# Get FTL: MV source files for reference
if args.dl:
    print('\n')
    print('------ Fetching FTL:MV source files ------------')
    if not os.path.isdir(SRC_FTL_MV_DIR):
        os.mkdir(SRC_FTL_MV_DIR)
    latest_mv_url = "https://drive.google.com/file/d/1FeSvVcrmnuJVP_0UMgcbpU50L9K-xGF2/view?usp=sharing"  # Always latest version according to devs
    output = f"{SRC_FTL_MV_DIR}/FTL-Multiverse-latest.zip"
    gdown.cached_download(latest_mv_url, output, quiet=False, fuzzy=True, postprocess=gdown.extractall)
elif not args.src and not os.path.isdir(f'{SRC_FTL_MV_DIR}/data'):
    print('No FTL:MV sources files provided ! Use "--dl" to fetch the latest version.')
    sys.exit()
elif os.path.isdir(f'{args.src}/data'):
    print(f'Trying with {args.src}/data folder')
elif os.path.isdir(f'{SRC_FTL_MV_DIR}/data'):
    print(f'Trying with existing {SRC_FTL_MV_DIR}/data folder')
elif args.src and not os.path.isdir(f'{args.src}/data'):
    print(f'{args.src} doesnt seems to be a valid FTL:Multiverse folder (No data/ folder inside).')
    sys.exit()

src_path = args.src if args.src else SRC_FTL_MV_DIR

print('\n')
print('------ Generating translated files ------------')
for po_file in tqdm(po_files, total=len(po_files), disable=args.debug):

    po_fname = os.path.basename(po_file)
    src_fname = os.path.splitext(po_fname)[0]

    # Glossary is only relevant for Weblate
    if src_fname == "glossary":
        continue

    po = None
    if args.debug:
        print(f"{src_fname} -> ", end="")
    try:
        po = polib.pofile(po_file)
    except IOError as e:
        print("Failed !")
        print(e)
        continue

    lang = po.metadata['Language']
    expected_src_file = f"{src_path}/data/{src_fname}"

    if not os.path.exists(expected_src_file):
        print("Failed !")
        print(f"{src_fname} not found in reference folder {src_path} ! Skipping")
        continue

    try:
        ftl_root = etree.parse(expected_src_file)
    except etree.XMLSyntaxError as e:
        print('Syntax Error in a reference XML file !')
        print(e)
        print('File unparseable, skipping...')
        continue

    if not os.path.isdir(f"{TEMP_TL_DIR}"):
        os.mkdir(f"{TEMP_TL_DIR}")
    out_path = os.path.join(f"{TEMP_TL_DIR}", f"{lang}/")
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

    if args.debug:
        print(f'{out_path}{src_fname}')
    ftl_root.write(f'{out_path}{src_fname}', pretty_print=True, encoding='utf-8')

print('\n')
print('------ Generating translated Mod Zips ----------')
print('(this step might take a while)')
for lang in os.listdir(f'{TEMP_TL_DIR}'):
    print(f'[{lang}]: ', end="")
    dest = f'{args.o}/{lang}/src/'
    if not os.path.isdir(dest):
        shutil.copytree(src_path, dest)
    else:
        print(f'{dest} exists already ! Skipping...')
        continue
    for tl_file in os.listdir(f'{TEMP_TL_DIR}/{lang}'):
        shutil.copy(f'{TEMP_TL_DIR}/{lang}/{tl_file}', f'{args.o}/{lang}/src/data/{tl_file}')
    shutil.make_archive(f'{args.o}/FTL-Multiverse-{lang}', 'zip', f'{args.o}/{lang}/src/')
    shutil.rmtree(f'{args.o}/{lang}', ignore_errors=True)
    print(f'Successfully generated {args.o}/FTL-Multiverse-{lang}.zip')

print('\n')
print('------ Cleaning temp files ---------------------')
if os.path.isdir(TEMP_TL_DIR):
    shutil.rmtree(f'{TEMP_TL_DIR}', ignore_errors=True)
if os.path.isdir(PO_EXTRACT_DIR):
    shutil.rmtree(f'{PO_EXTRACT_DIR}', ignore_errors=True)
if os.path.isdir(PO_EXTRACT_DIR):
    shutil.rmtree(f'{PO_EXTRACT_DIR}', ignore_errors=True)
print('All done !')
