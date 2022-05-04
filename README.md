# FTL: Multiverse i18n tools

[![FTL: Multiverse Logo](https://media.discordapp.net/attachments/649704076229083150/888254827845517343/banner5.png?width=837&height=282)]((https://subsetgames.com/forum/viewtopic.php?t=35332))

Tools to help translating the community mod [FTL: Multiverse](https://subsetgames.com/forum/viewtopic.php?t=35332)

- `ftl2po.py`: Generate `.pot` and `.po` translatable files based on any **FTL: Multiverse** version
- `po2ftl.py`: Generate translated **FTL: Multiverse** zips based on `.po` files.

You can help translating **FTL: Multiverse** on our [Weblate Project](https://weblate.hyperq.be/projects/ftlmultiverse/).

## Table of Content
  * [Prerequisites](#prerequisites)
  * [Setup](#setup)
  * [Usage](#usage)
    + [Import generated translations to Weblate](#import-generated-translations-to-weblate)
    + [Generate translated Mods from Weblate translations](#generate-translated-mods-from-weblate-translations)
    + [FTL2PO - PO2FTL](#ftl2po---po2ftl)
      - [ftl2po.py - Translatable Files Generator](#ftl2popy---translatable-files-generator)
        * [Other usages](#other-usages)
      - [po2ftl.py - Translated Mod Exporter](#po2ftlpy---translated-mod-exporter)
        * [Other Usages](#other-usages)
  * [Troubleshooting](#troubleshooting)
    + [Syntax Errors on source XML files](#syntax-errors-on-source-xml-files)
    + [Some translated terms in the XML files are skipped and therefore not present in the final PO files](#some-translated-terms-in-the-xml-files-are-skipped-and-therefore-not-present-in-the-final-po-files)
    + [See what files are failing](#see-what-files-are-failing)

## Prerequisites

- Python 3.8+

## Setup

* Clone this repository anywhere:
```console
> git clone https://github.com/arbaes/FTLMultiverse-i18n.git
```

* Install the requirements with pip
According to your Python setup, from the newly cloned directory either:
```console
> pip install -r requirements.txt
```
or
```console
> pip3 install -r requirements.txt
```
## Usage

Those tools were mainly created to help interact with our [Weblate Project](https://weblate.hyperq.be/projects/ftlmultiverse/).
### Import generated translations to Weblate

Generate translated files based on a existing already translated mod:

```console
> python ftl2po.py --dl --t-src path/to/translated_mod --t-lang fr
```

If you want to add your generate translatable files to our [Weblate Project](https://weblate.hyperq.be/projects/ftlmultiverse/) feel free to open a pull request on my [Upstream GitHub repository](https://github.com/arbaes/FTLMultiverse-generated-po).


### Generate translated Mods from Weblate translations
- Go to the [FTLMultiverse Weblate Project](https://weblate.hyperq.be/projects/ftlmultiverse/).
- Go to "Files" > "Download translation file as a ZIP file".

![Download Zip](https://i.imgur.com/DbNuAnE.png)
- Execute the following command:
```console
> python po2ftl.py --weblate-zip path/to/downloaded_zip --dl
```

By default, the generated zip will be placed in the `mods/` folder but you can change this by using the `-o` parameter.


### FTL2PO - PO2FTL

Those tools needs **FTL: Multiverse** source files as reference.
If you don't want to provide them both tools can automatically fetch them with the `--dl` flag
The source files will then be downloaded from [this link](https://drive.google.com/file/d/1FeSvVcrmnuJVP_0UMgcbpU50L9K-xGF2/view?usp=sharing) which should always be the latest **FTL:Multiverse** version.
#### ftl2po.py - Translatable Files Generator

Generate only `.pot` files based on the latest version:
```console
> python ftl2po.py --dl
```
Generate po files from an already translated Mod for the latest version
```console
> python ftl2po.py --dl --t-src path/to/translated_mod --t-lang <language code of translated mod>
```

e.g. french translated mod:
```console
> python ftl2po.py --dl --t-src path/to/translated_mod --t-lang fr
```

##### Other usages
```console
> python ftl2po.py -h
usage: ftl2po.py [-h] [--src PATH] [--t-src PATH] [--t-lang LANG] [-o PATH] [--skip-pot] [--debug] [--dl]

Generate FTL:MV Translatable files

options:
  -h, --help     show this help message and exit
  --src PATH     Path to the directory with source FTL:MV files.
  --t-src PATH   Path to the directory with already translated FTL:MV files.
  --t-lang LANG  Language of already translated FTL:MV files (to use with --t-src)
  -o PATH        Output directory
  --skip-pot     Skip the POT Templates files generation and try matching with existing ones (only used with --t-src)
  --debug        Verbose execution
  --dl           Download latest FTL: Multiverse as --src
```
#### po2ftl.py - Translated Mod Exporter

Generate mod zip from po files
```console
> python po2ftl.py --po-dir path/to/dir/with/.po/files --dl
```

Generate mod zip from Weblate zip file to a custom folder
```console
> python po2ftl.py --weblate-zip path/to/weblate/file.zip --dl -o ./translated_mods/
```

##### Other Usages

```console
> python po2ftl.py -h
usage: po2ftl.py [-h] [--src PATH] [--weblate-zip PATH] [--po-dir PATH] [-o PATH] [--debug] [--dl]

Generate FTL Translated files

options:
  -h, --help          show this help message and exit
  --src PATH          Path to the directory with FTL:MV Source files.
  --weblate-zip PATH  Path to a Weblate .zip file.
  --po-dir PATH       Path to the directory with translated PO files.
  -o PATH             Path to the Output directory.
  --debug             Verbose execution
  --dl                Download latest FTL: Multiverse as --src
  ```

## Troubleshooting
### Syntax Errors on source XML files

The parsing process being not as permissive as FTL, files can be skipped if there's any problem in their syntax.
Files have to be manually fixed to be processed, but fortunately it's generally not very hard to do.

Example with the `5.2.3` Version of **FTL: Multiverse**, this issue happen:
```console
Double hyphen within comment: <!--<event name="ALISON_MANTIS_CREW" unique="true">       <!, line 500, column 55 (events_mantis.xml.append, line 500)
```
This is because indeed, there's a second opening comment tag `<!--` inside a comment in the file `events_mantis.xml.append` on line `500`.
Simply delete it, save the file, and relaunch the script using the `--src` parameter.
```console
> python ftl2po.py --src src/  --t-src ../FTL-Multiverse-French-translation/ --t-lang fr
```

### Some translated terms in the XML files are skipped and therefore not present in the final PO files

This generally means the source **FTL:Multiverse** files used for reference are not in the same **version** than the XML files you are trying to export as PO.
Unfortunatly there's no way to determine what has changed between two versions and therefore you'll have to add them manually.
Keep in mind that the [Weblate Project](https://weblate.hyperq.be/projects/ftlmultiverse/) will always use the latest **FTL: Multiverse** version as reference.

### See what files are failing

You can use the `--debug` flag to see what files/nodes are failing to be processed
