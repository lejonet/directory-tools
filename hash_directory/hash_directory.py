#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Python stdlib
import sys, hashlib, os, multiprocessing, errno, types, logging, argparse

# "Defines" for the tuple that is put on the queue
FILE = 0
ROOT = 1

logger        = logging.getLogger()
streamhandler = logging.StreamHandler()
logger.addHandler(streamhandler)
logger.setLevel(logging.INFO)

try:
    walk = os.walk
except:
    walk = os.path.walk

def hash_directory(start_point, hashes_dir, only_hashes, size_hash):
    _create_hashes_directory(hashes_dir)
    
    manager    = multiprocessing.Manager()
    files_dict = manager.dict()
    queue      = manager.JoinableQueue()
    workers    = []

    for i in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=_worker, args=(queue, files_dict, "{}/hashes".format(hashes_dir), logger, size_hash))
        p.start()
        workers.append(p)

    _walk_directory(start_point, queue, files_dict)

    queue.join()
    for worker in workers:
        worker.terminate()

    _create_hashes_file(files_dict, start_point, hashes_dir)

def _create_hashes_file(files_dict, start_point, hashes_dir):
    dictionary = dict(files_dict)
    if sys.version_info.major < 3:
        iterator = dictionary.iteritems()
    else:
        iterator = dictionary.items()

    tuples = sorted(iterator, key=lambda data: data[1]["hash"])
    iterator = iter(tuples)

    with open("{}/hashes/{}.all_hashes".format(hashes_dir, start_point), "w") as f:
        for file, data in iterator:
            logger.debug("{} {}".format(file, data["hash"]))
            if only_hashes:
                f.write("{}\n".format(data["hash"]))
            else:
                f.write("{} {}\n".format(file, data["hash"]))

def _walk_directory(start_point, queue, files_dict):
    for root, dirs, files in walk(start_point):
        logger.info("In {}:".format(root))
        for file in files:
            logger.debug("{} {}".format(file, root))
            files_dict[file] = {"path": "{}/{}".format(root, file)}
            queue.put((file, root))

def _create_hashes_directory(hashes_dir):
    try:
        os.makedirs("{}/hashes".format(hashes_dir))
    except IOError as e:
        if e.errno == errno.EACCESS:
            logger.error("Cannot access {}, please give a directory which you have read/write access too".format(hashes_dir))
            sys.exit(1)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e.strerror)
            sys.exit(1)

def _hash_file(file, hasher, size_to_hash, blocksize=2**17):
    buf = file.read(blocksize)
    while len(buf) > 0 and file.tell() <= size_to_hash and buf != '':
        hasher.update(buf)
        buf = file.read(blocksize)
    return hasher.hexdigest()

def _worker(queue, files, hashes_dir, logger, size_to_hash):
    while True:
        item = queue.get()
        file_path = "{}/{}".format(item[ROOT], item[FILE])
        directory = "{}/{}".format(hashes_dir, item[ROOT])
        try:
            os.makedirs(directory)
        except (IOError, OSError) as e:
            if e.errno != errno.EEXIST:
                logger.warning("Error {} happened while processing {}, skipping...".format(e.strerror, file_path))
                continue

        hash_file_path = "{}/_{}".format(directory, item[FILE])
        file_dict = files[item[FILE]] # Apparently Manager.dict() types doesn't support updating
                                      # values in nested dict's, so have to take it out locally
                                      # and edit it and then put it back as the value in the manager
                                      # dict
        if not os.path.isfile(hash_file_path):
            with open(hash_file_path, "w") as out_file:
                with open(file_path, "rb") as in_file:
                    hasher = hashlib.sha256()
                    hash = _hash_file(in_file, hasher, size_to_hash)
                    file_dict["hash"] = hash
                    out_file.write("{}\n".format(hash))
        else:
            with open(hash_file_path, "r") as in_file:
                hash = in_file.readline().rstrip()
                file_dict["hash"] = hash
        
        files[item[FILE]] = file_dict
        logger.debug("Root: {} File: {} Hash: {} Path: {}".format(item[ROOT], item[FILE], files[item[FILE]]["hash"], files[item[FILE]]["path"]))
        queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scans a directory structure and hashes all the files in it")
    parser.add_argument("--debug", "-d", help="turns on debug messages", action="store_true")
    parser.add_argument("--only-hashes", "-o", help="only outputs the hashes into the file with all hashes", action="store_true")
    parser.add_argument("--log-to-file", "-f", type=str, help="will also log information to log_file, in addition to stdout/stderr")
    parser.add_argument("--size-hash", "-s", type=int, help="the amount, in kB, that should be hashed of the files (default 256kB)", dest="size_hash")
    parser.add_argument("start_point", type=str, help="the directory to start the recursive walk at")
    parser.add_argument("hashes_dir", type=str, help="the directory where the directory structure will be copied and hashes stored")

    args = parser.parse_args()
    only_hashes   = args.only_hashes
    debug         = args.debug
    size_hash     = args.size_hash * 1024 if args.size_hash else 256 * 1024
    start_point   = args.start_point
    hashes_dir    = args.hashes_dir
    log_file      = args.log_to_file

    if log_file:
        filehandler = logging.FileHandler(log_file)
        logger.addHandler(filehandler)

    if debug:
        logger.setLevel(logging.DEBUG)

    hash_directory(start_point, hashes_dir, only_hashes, size_hash)

