import os
import sys
import argparse

import gdown
import polib
from lxml import etree
from tqdm import tqdm


SRC_FTL_MV_DIR = 'src'
MV_VERSION = "5.0"
EXCLUDED_TAGS = [
    'autoReward',
    'aggressive',
    'playSound',
    'changeBackground',
    'customFleet',
    'choice',
    'img',
    'fleet'
]

parser = argparse.ArgumentParser(description='Generate FTL:MV Translatable files')
parser.add_argument('--src', action='store', type=str, metavar='PATH', help='Path to the directory with source FTL:MV files.')
parser.add_argument('--t-src', action='store', type=str, metavar='PATH', help='Path to the directory with already translated FTL:MV files.')
parser.add_argument('--t-lang', action='store', type=str, metavar='LANG', help='Language of already translated FTL:MV files (to use with --t-src)')
parser.add_argument('-o', action='store', metavar='PATH', type=str, help='Output directory', default='po')
parser.add_argument('--skip-pot', action='store_true', help='Skip the POT Templates files generation and try matching with existing ones (only used with --t-src)')
parser.add_argument('--debug', action='store_true', help='Verbose execution')
parser.add_argument('--dl', action='store_true', help='Download latest FTL: Multiverse as --src')
args = parser.parse_args()


# Generate unique ID that will allow to retrieve the exact position
# of text in the original source files to generate the translated source
def generate_text_id(root, node):
    full_xpath = root.getpath(node)
    relative_xpath = None

    tags = ["event", "eventList", "textList", "ship"]
    for tag in tags:
        try:
            base_node = node if node.get('name') else node.xpath(f'ancestor::{tag}[@name]')[-1]
            base_node_xpath = root.getpath(base_node)
            relative_xpath = full_xpath.replace(base_node_xpath, f"{base_node.tag}__{base_node.get('name')}__")
        except:
            pass

    if not relative_xpath:
        raise NameError(f"Cannot generate translation ID for {root.getpath(node)}!")

    return relative_xpath


# Main Parser
def generate_pot_files(path):
    print('\n')
    print('------ Generating .pot template files ---------')

    files = os.listdir(f'{path}/data')
    for f_name in tqdm(files, unit="files", total=len(files), disable=args.debug):

        # Only valid text files that I'm aware of.
        ext = f_name.split('.')[-1]
        if not ((ext == 'xml' or ext == 'append') and "event" in f_name):
            continue

        try:
            ftl_root = etree.parse(f"{path}/data/{f_name}")
        except etree.XMLSyntaxError as e:
            print('Syntax Error in a reference XML file !')
            print(e)
            print('File unparseable, skipping...')
            continue

        build_text_list = etree.XPath("//text()")
        all_txt_nodes = build_text_list(ftl_root)

        translatable_nodes = []
        for el in all_txt_nodes:
            if len(el.strip()) > 0 \
                and not (el.isupper() and '_' in el) \
                    and el.getparent().tag not in EXCLUDED_TAGS \
                    and el != 'true' and el != 'false':
                translatable_nodes.append(el.getparent())

        # Skip file if no text nodes
        if len(translatable_nodes) < 1:
            continue

        if args.debug:
            print(f'{f_name}: ', end="")

        filepath = f"{args.o}/{f_name}.pot"
        with open(filepath, "w", encoding="UTF-8") as fo:
            fo.write(f"# FTL MULTIVERSE {MV_VERSION} - {f_name}\n\n")

            nb_texts = 0
            for tn in translatable_nodes:

                # There's sometimes empty texts for technical purposes
                if not tn.text:
                    continue

                text_esc = tn.text.replace('"', '\\"')
                fo.write(f"#: {f_name}\n")
                msgctxt = generate_text_id(ftl_root, tn)
                fo.write(f'msgctxt "{msgctxt}"\n')
                if '\n' not in text_esc:
                    fo.write(f'msgid "{text_esc}"\n')
                    nb_texts += 1
                else:
                    fo.write('msgid ""\n')
                    lines = text_esc.split('\n')
                    for line in lines:
                        if len(line) > 1:
                            fo.write(f'  "{line}"\n')
                    fo.write('\n')
                fo.write('msgstr ""\n\n')

            fo.close()
            if args.debug:
                print(f"{nb_texts} texts converted")


# Based on previously generated .pot files
def generate_translated_po(src_path, pot_path, lang):
    print('\n')
    print(f'------ Generating [{lang}] .po files --------------')

    tot_nb_translated = []
    tot_nb_failed = []
    tot_nb_duplicates = []

    files = os.listdir(f"{src_path}/data")
    for f_name in tqdm(files, unit="files", total=len(files), disable=args.debug):

        # Only valid text files that I'm aware of.
        ext = f_name.split('.')[-1]
        if not ((ext == 'xml' or ext == 'append') and "event" in f_name):
            continue

        try:
            lang_root = etree.parse(f"{src_path}/data/{f_name}")
        except etree.XMLSyntaxError as e:
            print('Syntax Error in a reference XML file !')
            print(e)
            print('File unparseable, skipping...')
            continue

        build_text_list = etree.XPath("//text()")
        all_txt_nodes = build_text_list(lang_root)

        translatable_nodes = []
        for el in all_txt_nodes:
            if len(el.strip()) > 0 \
                and not (el.isupper() and '_' in el) \
                    and el.getparent().tag not in EXCLUDED_TAGS \
                    and el != 'true' and el != 'false':
                translatable_nodes.append(el.getparent())

        # Skip file if no text nodes
        if len(translatable_nodes) < 1:
            continue

        if args.debug:
            print(f'{f_name}: ', end="")

        expected_pot_file = f"{pot_path}/{f_name}.pot"
        if not os.path.exists(expected_pot_file):
            if args.debug:
                print('Not found')
            continue

        try:
            po = polib.pofile(expected_pot_file)
        except IOError as e:
            print(f"{expected_pot_file} can't be parsed")
            print(e)

        po.metadata = {
            'Project-Id-Version': '1.0',
            'Language': f'{lang}',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }

        nb_translated = 0
        nb_failed = 0
        nb_duplicates = 0

        for tn in translatable_nodes:
            # There's sometimes empty texts for technical purposes
            if not tn.text:
                continue
            gen_msgctxt = generate_text_id(lang_root, tn)
            poe_matched = [entry for entry in po if entry.msgctxt == gen_msgctxt]
            if 0 < len(poe_matched):
                # It seems the mission are sometimes duplicated in the source FTL:MV Files
                # So we translate everything and hope for the best
                nb_duplicates += len(poe_matched) - 1
                for poe in poe_matched:
                    poe.msgstr = tn.text
                    nb_translated += 1
            else:
                if args.debug:
                    print(f"{gen_msgctxt} not found in source .POT file, skipping...")
                nb_failed += 1
                continue

        po.save(f"{pot_path}/{f_name}.po")

        tot_nb_translated.append(nb_translated)
        tot_nb_failed.append(nb_failed)
        tot_nb_duplicates.append(nb_duplicates)

        if args.debug:
            print(f"Translated: {nb_translated} | Failed: {nb_failed}")
    if not args.debug:
        print(f"Translated: {sum(tot_nb_translated)} | Failed: {sum(tot_nb_failed)}")


print("FTL: Multiverse Translatable Files Generator  ")
print("==============================================")

# Validity Checks
gen_po = False
if args.t_src and not args.t_lang:
    print('Please specify a language with --t-lang')
    sys.exit()
elif not args.t_src and args.t_lang:
    print('Please specify a translated source with --t-src')
    sys.exit()
elif args.t_src and args.t_lang:
    if not os.path.isdir(args.t_src) or not os.path.isdir(f'{args.t_src}/data'):
        print(f'{args.t_src} is not a valid directory')
    else:
        gen_po = True


if not os.path.isdir(f"{args.o}"):
    os.mkdir(f"{args.o}")

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


if not args.skip_pot:
    generate_pot_files(src_path)
if gen_po:
    generate_translated_po(args.t_src, args.o, args.t_lang)

print('\n')
print('All done !')
