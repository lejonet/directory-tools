#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys, hashlib, os, multiprocessing, errno, types, logging
FILE = 0
ROOT = 1

try:
    walk = os.walk
except:
    walk = os.path.walk

if len(sys.argv) != 3:
    print("Usage: {} <directory to scan for files to hash> <where to create directory that will hold the hashes>".format(sys.argv[0]))
    sys.exit(1)

manager     = multiprocessing.Manager()
start_point = sys.argv[1]
hashes_dir  = sys.argv[2]
files_dict  = manager.dict()
logger      = logging.getLogger()
filehandler   = logging.FileHandler("{}/hashes/worker.log".format(hashes_dir))
streamhandler = logging.StreamHandler()
logger.addHandler(filehandler)
logger.addHandler(streamhandler)
logger.setLevel(logging.INFO)

try:
    os.makedirs(hashes_dir+"/hashes")
except IOError as e:
    if e.errno == errno.EACCESS:
        logger.error("Cannot access {}, please give a directory which you have read/write access too".format(hashes_dir))
        sys.exit(1)
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e.strerror)
        sys.exit(1)

queue   = manager.JoinableQueue()
workers = []

def hash_file(file, hasher, blocksize=2**16):
    buf = file.read(blocksize)
    while len(buf) > 0 and file.tell() <= blocksize*64000 and buf != '': # 64kB * 64000 = 4MB
        hasher.update(buf)
        buf = file.read(blocksize)
    return hasher.hexdigest()

def worker(queue, files, hashes_dir, logger):
    hasher = hashlib.sha256()
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
                with open(file_path, "r") as in_file:
                    hash = hash_file(in_file, hasher)
                    file_dict["hash"] = hash
                    out_file.write("{}\n".format(hash))
        else:
            with open(hash_file_path, "r") as in_file:
                hash = in_file.readline().rstrip()
                file_dict["hash"] = hash
        
        files[item[FILE]] = file_dict
        logger.debug("Root: {} File: {} Hash: {} Path: {}".format(item[ROOT], item[FILE], files[item[FILE]]["hash"], files[item[FILE]]["path"]))
        queue.task_done()


for i in range(multiprocessing.cpu_count()):
    p = multiprocessing.Process(target=worker, args=(queue, files_dict, hashes_dir+"/hashes", logger))
    p.start()
    workers.append(p)

for root, dirs, files in walk(start_point):
    logger.info("In {}:".format(root))
    for file in files:
#        print("{} {}".format(file, root))
        files_dict[file] = {"path": "{}/{}".format(root, file)}
        queue.put((file, root))

queue.join()
for worker in workers:
    worker.terminate()

if sys.version_info.major < 3:
    iterator = files_dict.items()
else:
    iterator = files_dict.iteritems()

with open("{}/hashes/all_hashes".format(hashes_dir), "w") as f:
    for key, value in iterator:
        logger.info("{} {}".format(key, value["hash"]))
        f.write("{} {}\n".format(key, value["hash"]))
