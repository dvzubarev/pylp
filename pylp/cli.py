#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path

from pylp.converter_conll_ud_v1 import ConverterConllUDV1
from pylp import lp_doc


def convert_cli(args):
    conv = ConverterConllUDV1()

    txt_file_path = Path(args.input_file_prefix + '.txt')
    if not txt_file_path.exists():
        raise RuntimeError(f"{txt_file_path} does not exist")

    conll_file_path = Path(args.input_file_prefix + '.conll')
    if not conll_file_path.exists():
        raise RuntimeError(f"{conll_file_path} does not exist")
    with (
        open(txt_file_path, 'r', encoding='utf8') as txtf,
        open(conll_file_path, 'r', encoding='utf8') as conllf,
    ):
        doc = lp_doc.Doc('0')
        conv(txtf.read(), conllf.read(), doc)

        print(doc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default=False)

    subparsers = parser.add_subparsers(help='sub-command help')

    prepare_convert = subparsers.add_parser('convert')
    prepare_convert.add_argument("--input_file_prefix", "-i", required=True)

    prepare_convert.set_defaults(func=convert_cli)

    args = parser.parse_args()

    FORMAT = "%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format=FORMAT)
    try:
        args.func(args)
    except Exception as e:
        logging.exception("failed to convert: %s ", e)


if __name__ == '__main__':
    main()
