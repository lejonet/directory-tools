#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Python stdlib
import argparse, logging, os, errno, sys, shutil, mimetypes, filecmp

# External
import magic

try:
    walk = os.walk
except:
    walk = os.path.walk

logger        = logging.getLogger()
streamhandler = logging.StreamHandler()
logger.addHandler(streamhandler)

def sort_directory(target_directory, sorted_directory):
    _create_sorted_directory(sorted_directory, target_directory)
    for root, dirs, files in walk(target_directory):
        logger.info("In {}:".format(root))
        for file in files:
            file_path = "{}/{}".format(root, file)

            store_dir = _find_store_dir(file_path)
            file_target_dir = "{}/sorted-{}/{}".format(sorted_directory, target_directory, store_dir)
            try:
                os.mkdir(file_target_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    if logger: logger.warning("File {} was not moved due to: {}".format(file, str(e)))
                    continue
    
            file_target_path = "{}/{}".format(file_target_dir, file)
            if not (os.path.isfile(file_target_path) and filecmp.cmp(file_path, file_target_path, shallow=False)):
                shutil.copy2(file_path, file_target_path)

def _find_store_dir(file_path):
    mime = magic.from_file(file_path, mime=True)
    store_dir = None

    if mime in ['application/octet-stream', 'text/plain'] or mimetypes.guess_extension(mime) == None:
        store_dir = os.path.splitext(file_path)[1]
    else:
        store_dir = mimetypes.guess_extension(mime)
    
    return store_dir.lstrip(".").lower()

def _create_sorted_directory(sorted_directory, target_directory):
    try:
        os.makedirs("{}/sorted-{}".format(sorted_directory, target_directory))
    except IOError as e:
        if e.errno == errno.EACCESS:
            if logger: logger.error("Cannot access {}, please give a directory which you have read/write access too".format(sorted_directory))
            sys.exit(1)
    except OSError as e:
        if e.errno != errno.EEXIST:
            if logger: logger.error(str(e))
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sorts a directory, recursively, by filetype")
    parser.add_argument("target_directory", type=str, help="the directory to be sorted")
    parser.add_argument("sorted_directory", type=str, help="the directory where the sorted directory will be created in")
    parser.add_argument("--log-to-file", "-f", type=str, dest="log_file", help="will also log information to log_file, in addition to stdout/stderr")
    parser.add_argument("--debug", "-d", action="store_true", help="adds more verbose logging")

    args = parser.parse_args()
    target_directory = args.target_directory
    sorted_directory = args.sorted_directory
    log_file         = args.log_file
    debug            = args.debug

    if log_file:
        filehandler = logging.FileHandler(log_file)
        logger.addHandler(filehandler)

    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logger.setLevel(log_level)

    sort_directory(target_directory, sorted_directory)

