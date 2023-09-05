# unique-files
Simple python script to find, and potentially replace, duplicate files in a directory, by grouping files by a hash.
Main focus is optimizations in hashing.
For example, current version first uses a ``hash`` which is file size, since on most file systems this does not require reading any of the contents of the file and is thus much faster.

Very much a work in progress; complete documention will be written once options/scope stablize.
