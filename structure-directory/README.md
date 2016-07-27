Usage
=====
`structure-directory.py <directory to be copied from, recursively> <directory where the files should be copied, in subfolders based on file type>`

There is also a few flags:
+ -f, --log-to-file log_file, logs all output to log_file in addition to stdout/stderr logging
+ -d, --debug, turns on very verbose logging

Example
=======
`./structure-directory.py /tmp /home/tmp

It will enumerate all the files, recursively, in /tmp and use a combination of mimetypes and python-magic to figure out what filetype each file is, and makes a subdirectory with the name of the file extension and puts the file in it. Due to shutil's incapability of preserving owner/group and ACLs, if such things are important, they'll have to be dealt with manually.

Dependencies
============
Outside of python stdlib, this script depends on [python-magic](https://github.com/ahupp/python-magic)
