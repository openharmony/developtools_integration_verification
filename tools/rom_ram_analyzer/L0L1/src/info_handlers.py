import logging
from typing import *
import preprocess
from pkgs.gn_common_tool import GnVariableParser


def extension_handler(paragraph: Text):
    return GnVariableParser.string_parser("output_extension", paragraph).strip('"')


def hap_name_handler(paragraph: Text):
    return GnVariableParser.string_parser("hap_name", paragraph).strip('"')


def target_type_handler(paragraph: Text):
    tt = GnVariableParser.string_parser("target_type", paragraph).strip('"')
    if not tt:
        logging.warning("parse 'target_type' failed, maybe it's a variable")
    return tt
