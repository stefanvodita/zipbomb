import os
import sys

from zipfile import ZipFile


def unzip(path=os.path.abspath(os.getcwd()), depth=0, remove=0):
    """
    @param path: absolute path to a file you want to recursively unzip
    @param remove: 0 - do not remove archives after unzipping them
                   1 - keep only the first archive encountered (the root most likely)
                   2 - delete all archives
    """
    if depth <= 0:
        return

    print("Unzipping", path)

    if os.path.isdir(path):
        files = os.listdir(path)    # more could be created by unzipping
        for f in files:
            unzip(os.path.join(path, f), depth - 1, remove)

    if os.path.isfile(path) and path[-4:] == ".zip":
        with ZipFile(path, "r") as root:
            root.printdir()
            root.extractall(path=path[:-4])

            if remove == 0:
                unzip(path[:-4], depth, 0)
            elif remove == 1:
                unzip(path[:-4], depth, 2)
            elif remove == 2:
                print("Removing", path)
                os.remove(path)
                unzip(path[:-4], depth, 2)
            else:
                print("Invalid remove option")
                return


if __name__ == "__main__":
    unzip(os.path.join(os.path.abspath(os.getcwd()), sys.argv[1]),
          int(sys.argv[2]),
          int(sys.argv[3]))
