Usage
=====
`hash-directory.py <directory to scan for files to hash> <where to create directory that will hold the hashes>`
There's also a few flags:
--debug, turns on very verbose logging
--only-hashes, writes only the hashes into the all_hashes file, instead of file hash pairs, which is default
-h, --help, shows usage directions

Example
=====
./hash-directory.py /tmp /home/tmp

It will enumerate all the files, recursively, in /tmp and replicate the directory hierarchy in /home/tmp and place a file with the name `_<filename>` at the same place in the hierarchy as it finds it, but the content will be the hash of the first 4MB of the file.
It will put all the hashes, paired with the filename of the file the hash belongs to, in `/home/tmp/hashes/<directory name>.all_hashes` for easier diffing between directories.
