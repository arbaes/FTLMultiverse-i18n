import os
import sys
import argparse

import polib
from lxml import etree

MV_DATA_PATH = 'data_src/'
MV_VERSION = "5.2.3"

parser = argparse.ArgumentParser(description='Generate FTL:MV Translatable files')
parser.add_argument('--src', action='store', type=str, metavar='PATH', help='Path to the directory with source FTL:MV files.', default="data_src/")
parser.add_argument('--t-src', action='store', type=str, metavar='PATH', help='Path to the directory with already translated FTL:MV files.')
parser.add_argument('--t-lang', action='store', type=str, metavar='LANG', help='Language of already translated FTL:MV files (to use with --t-src)')
parser.add_argument('-o', action='store', metavar='PATH', type=str, help='Output directory', default='po/')
parser.add_argument('--skip-pot', action='store_true', help='Skip the POT Templates files generation and try matching with existing ones (only used with --t-src)')
args = parser.parse_args()


if not os.path.isdir(args.src):
    print(f'{args.src} is not a valid directory')
    sys.exit()

gen_po = False
if args.t_src and not args.t_lang:
    print('Please specify a language with --t-lang')
    sys.exit()
elif not args.t_src and args.t_lang:
    print('Please specify a translated source with --t-src')
    sys.exit()
elif args.t_src and args.t_lang:
    if not os.path.isdir(args.t_src):
        print(f'{args.t_src} is not a valid directory')
    else:
        args.t_src = args.t_src if args.t_src[-1] == "/" else f"{args.t_src}/"
        gen_po = True


if not os.path.isdir(f"{args.o}"):
    os.mkdir(f"{args.o}")

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
    print('Generating .pot template files....')
    print("==================================")
    translatable_tags = set()
    files = os.listdir(path)
    for f_name in files:

        # Only valid text files that I'm aware of.
        ext = f_name.split('.')[-1]
        if not ((ext == 'xml' or ext == 'append') and "event" in f_name):
            continue

        ftl_root = etree.parse(f"{path}{f_name}")
        text_nodes = ftl_root.findall('//text')
        build_text_list = etree.XPath("//text()")
        all_txt_nodes = build_text_list(ftl_root)

        excluded_tags = [
            'autoReward',
            'aggressive',
            'playSound',
            'changeBackground',
            'customFleet',
            'choice',
            'img'
        ]

        translatable_nodes = []
        for el in all_txt_nodes:
            if len(el.strip()) > 0 \
                and not (el.isupper() and '_' in el) \
                and el.getparent().tag not in excluded_tags \
                and el != 'true' and el != 'false':
                translatable_nodes.append(el.getparent())

        # Skip file if no text nodes
        if len(translatable_nodes) < 1:
            continue

        print(f'{f_name}: ', end="")

        filepath = f"{args.o}{f_name}.pot"
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
                if not '\n' in text_esc:
                    fo.write(f'msgid "{text_esc}"\n')
                    nb_texts += 1
                else:
                    fo.write(f'msgid ""\n')
                    lines = text_esc.split('\n')
                    for l in lines:
                        if len(l) > 1:
                            fo.write(f'  "{l}"\n')
                    fo.write('\n')
                fo.write(f'msgstr ""\n\n')

            fo.close()
            print(f"{nb_texts} texts converted")


def generate_translated_po(src_path, pot_path, lang):
    print(f'Generating [{lang}] .po files...')
    print("==================================")
    files = os.listdir(src_path)
    for f_name in files:

        # Only valid text files that I'm aware of.
        ext = f_name.split('.')[-1]
        if not ((ext == 'xml' or ext == 'append') and "event" in f_name):
            continue

        lang_root = etree.parse(f"{src_path}{f_name}")
        text_nodes = lang_root.findall('//text')

        # Skip file if no text nodes
        if len(text_nodes) < 1:
            continue

        print(f'{f_name}: ', end="")

        expected_pot_file = f"{pot_path}{f_name}.pot"
        if not os.path.exists(expected_pot_file):
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
        for tn in text_nodes:
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
                print(f"{gen_msgctxt} not found in source .POT file, skipping...")
                nb_failed += 1
                continue


        po.save(f"{pot_path}{f_name}.po")
        print(f"Translated: {nb_translated} | Failed: {nb_failed}")


if not args.skip_pot:
    generate_pot_files(args.src)
print('- - - - - - - - - - - - - - - - - - - ')
if gen_po:
    generate_translated_po(args.t_src, args.o, args.t_lang)
