#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import argparse, logging, os, errno, sys

parser = argparse.ArgumentParser(description="Sorts a directory, recursively, by filetype")
parser.add_argument("target_directory", type=str, help="the directory to be sorted")
parser.add_argument("sorted_directory", type=str, help="the directory where the sorted directory will be created in")
parser.add_argument("--log-to-file", "-f", type=str, dest="log_file", help="will also log information to log_file, in addition to stdout/stderr")
parser.add_argument("--debug", "-d", type=bool, action="store_true", help="adds more verbose logging")

args = parser.parse_args()

target_directory = args.target_directory
sorted_directory = args.sorted_directory
log_file         = args.log_file
debug            = args.debug

logger        = logging.getLogger()
streamhandler = logging.StreamHandler()
logger.addHandler(streamhandler)

if log_file:
    filehandler = logging.FileHandler(log_file)
    logger.addHandler(filehandler)

if debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logger.setLevel(log_level)

try:
    walk = os.walk
except:
    walk = os.path.walk

try:
    os.makedirs("{}/sorted-{}".format(sorted_directory, target_directory))
except IOError as e:
    if e.errno == errno.EACCESS:
        logger.error("Cannot access {}, please give a directory which you have read/write access too".format(sorted_directory))
        sys.exit(1)
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(str(e))
        sys.exit(1)


