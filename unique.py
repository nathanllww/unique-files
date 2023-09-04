import os
import hashlib
from time import sleep
import time
import random
import string
import sys

# generate n files with a randomly choosen number between k and 3k characters choosen randomly from a-z each
def generate_random_files(n, k):
    for i in range(n):
        k2 = random.randint(k, 10*k)
        with open(f"test{i}.txt", 'w') as f:
            f.write(''.join(random.choice(string.ascii_lowercase) for _ in range(k2)))

# get_hash takes a file path and returns the md5 hash of the file
def get_hash(path):
    try:
        with open(path, 'rb') as f:
            # return hashlib.md5(f.read()).hexdigest()
            return str(hash(f.read()))
    except PermissionError:
        print(f"Permission denied: {path}")
        return None

def read_bits(path, k, startpoint = 0, offset = 0):
    try:
        with open(path, 'rb') as f:
            # f.seek(random.randint(0, os.path.getsize(path) - k))
            f.seek(startpoint)
            a = f.read(k)
            if offset > 0:
                f.seek(startpoint + offset)
                b = f.read(k)
                return a + b
            else:
                return a
    except PermissionError:
        print(f"Permission denied: {path}")
        return None

# function find_all lists all files in any subdirectory of the current directory
def find_all(path, skip_hidden=True, testing_old=False):
    if not testing_old:
        return find_all_scandir(path, skip_hidden=skip_hidden)
    else:
        result = []
        for root, dirs, files in os.walk(path, followlinks=False):
            if skip_hidden:
                files = [f for f in files if not f[0] == '.']
                dirs[:] = [d for d in dirs if not d[0] == '.']

            for name in files:
                result.append(os.path.join(root, name))
        return result

# get sizes of all files in dir
def get_sizes(path):
    return [os.path.getsize(f) for f in find_all(path)]

# recursively list all files in a directory using os.scandir
def find_all_scandir(path, skip_hidden=True):
    result = []
    for entry in os.scandir(path):
        try:
            if entry.is_dir(follow_symlinks=False) and (not skip_hidden or not entry.name[0] == '.'):
                result += find_all_scandir(entry.path)
            elif not entry.is_dir() and (skip_hidden or not entry.name[0] == '.'):
                result.append(entry.path)
        except PermissionError:
            print(f"Permission denied: {entry.path}")
    return result


# unique_hashes_and_files returns a tuple (hash_dict, files_point, files)
def unique_hashes_and_files(path):
    files = find_all(path, skip_hidden=True)
    hashes = [get_hash(f) for f in files]
    # create a dict hash_dict where every key is a hash and every value is a list of files with that hash
    hash_dict = {}
    for i in range(len(hashes)):
        if hashes[i] in hash_dict:
            hash_dict[hashes[i]].append(files[i])
        else:
            hash_dict[hashes[i]] = [files[i]]
    files_point = [hash_dict[hashes[i]][0] for i in range(len(hashes))]

    # if files_point[i] has the same hash as files_point[j] and j < i, replace files_point[i] with a symlink to files_point[j]
    # for i in range(len(files_point)):
    #     for j in range(i):
    #         if hashes[i] == hashes[j]:
    #             # print(f"found duplicate: {files_point[i]}")
    #             # print(f"replacing with symlink to {files_point[j]}")
    #             # os.remove(files_point[i])
    #             # os.symlink(files_point[j], files_point[i])
    #             files_point[i] = files_point[j]
    #             break

                # else:
                #     print(f"duplicate file found: {pf}")
                # results.append(hashlib.md5(f.read()).hexdigest())
    return (hash_dict, files_point, files)
    # might want to make this just return hash_dict in the future

# determine all files with the same size in a directory
def same_size_files(path, use_index=False):
    files = find_all_scandir(path, skip_hidden=True)
    files.sort()
    sizes = [os.path.getsize(f) for f in files]
    size_dict = {}
    for i in range(len(sizes)):
        if sizes[i] in size_dict:
            if use_index:
                size_dict[sizes[i]].append(i)
            else:
                size_dict[sizes[i]].append(files[i])
        else:
            if use_index:
                size_dict[sizes[i]] = [i]
            else:
                size_dict[sizes[i]] = [files[i]]
    return (size_dict, files)

# for all files in a directory with the same file size, compare their hashes
def same_size_same_hash(path, prnt=False, hash_fun=get_hash):
    size_dict, files = same_size_files(path)
    count = len(files)
    unique_sizes = len(size_dict)
    real_dict = {}
    for size in size_dict:
        if len(size_dict[size]) > 1:
            l = size_dict[size]
            # using string to avoid any overlap with sizes and hashes (honestly seems unlikely)
            hashes = [str(hash_fun(l[i])) for i in range(len(l))]
            # hash_dict = {}
            for i in range(len(hashes)):
                if hashes[i] in real_dict:
                    real_dict[hashes[i]].append(l[i])
                    count -= 1
                else:
                    real_dict[hashes[i]] = [l[i]]
            if len(set(hashes)) == len(l) and prnt:
                print(f"same size, different hashes: {size_dict[size]}")
        else:
            real_dict[size] = size_dict[size]
    return (real_dict, files, count, unique_sizes)

# given a path and a list of hash functions, compare all files with the first function. If there are any collisions, compare the files with the second function, and so on.
# hash functions should have different return types, or at least never collide with each other
# to make cleaner, first comparsions are done via file size
def unique_via_comparsions(path, hash_funs=[os.path.getsize, get_hash]):
    files = find_all_scandir(path, skip_hidden=True)
    d, counts = unique_via_comparsions_files(files, hash_funs)
    return (d, files, counts)

def convert_hash_lists_to_dicts(hashes, files):
    d = {}
    for i in range(len(hashes)):
        if hashes[i] in d:
            d[hashes[i]].append(files[i])
        else:
            d[hashes[i]] = [files[i]]
    return d

def unique_via_comparsions_files(files, hash_funs):
    files_to_hash = range(len(files))
    complete_dict = {}
    counts = [0] * len(hash_funs)
    for j in range(len(hash_funs)):
        fun = hash_funs[j]
        hashes = [fun(files[i]) for i in files_to_hash]
        hash_dict = convert_hash_lists_to_dicts(hashes, files_to_hash)
        complete_dict = complete_dict | hash_dict

        new_hashing = []
        for h in hash_dict:
            if len(hash_dict[h]) > 1:
                new_hashing += hash_dict[h]
                if j < len(hash_funs) - 1:
                    complete_dict.pop(h)
        files_to_hash = new_hashing
        counts[j] = len(files_to_hash)
        if len(files_to_hash) == 0:
            break
    return complete_dict, counts

def determine_links(files, dirs_to_replace):
    to_remove = []
    for f in files:
        # containing_dir = os.path.dirname(f)
        for d in dirs_to_replace:
            if os.path.abspath(f).startswith(d):
                to_remove.append(f)
                break
    return to_remove

def create_links(files, to_replace):
    count = 0
    if files == to_replace:
        fkeep = files[0]
    else:
        for f in files:
            if f not in to_replace:
                fkeep = f
                break

    fkeep_abspath = os.path.abspath(fkeep)
    for f in files:
        if f in to_replace and f is not fkeep:
            os.remove(f)
            os.symlink(fkeep_abspath, f)
            count += 1
    return count

def determine_and_replace(files, dirs_to_replace, replace_all):
    if dirs_to_replace is None and replace_all == False:
        return 0
    elif dirs_to_replace is None: #replace_all must be true
        return create_links(files, files)
    else:
        to_replace = determine_links(files, dirs_to_replace)
        return create_links(files, to_replace)



########### BEGIN SCRIPT ###########

dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
dir = os.getcwd()
replace_all = False
dirs_to_replace = None
if len(sys.argv) > 1:
    dir = sys.argv[1]
    if not os.path.isdir(dir):
        print("Not a valid directory")
        exit(1)
    if len(sys.argv) > 2:
        if sys.argv[2] == '--replace-all':
            replace_all = True
        elif sys.argv[2] == '--dirs-to-replace':
            dirs_to_replace = [os.path.abspath(f) for f in sys.argv[3:]]
            # TODO: currently using abspaths for everything symlink related
            # this ensures symlinks work, but it does not make portability good
            # look into whether some sort of relative symlink is best here
        else:
            print("Invalid argument: " + sys.argv[2])
            exit(1)

start_time = time.time()
seed = random.randint(0, 100)
offset = 0
f = lambda x : read_bits(x, 1000, startpoint=seed, offset=offset)
(d, files, counts) = unique_via_comparsions(dir, hash_funs=[os.path.getsize, f, get_hash])
end_time = time.time()
print(f"Time elapsed for sizes and file size: {end_time - start_time}")
print(f"Total files: {len(files)}")
print(f"Total unique: {len(d)}")
for i in range(len(counts)):
    print(f"Number of files after {i+1} hash functions: {counts[i]} ({counts[i]/len(files)*100:.2f}%)")
print("")

if not (dirs_to_replace is None and replace_all == False):
    print(f"At this stage, the program will attempt to replace duplicate files with symlinks. Are you sure you want to continue? [y/N]")
    ans = input()
    if ans == 'y':
        replace_count = 0
        for key in d:
            if len(d[key]) > 1:
                fs = [files[i] for i in d[key]]
                replace_count += determine_and_replace(fs, dirs_to_replace, replace_all)
        print(f"Total replaced files: {replace_count}")
