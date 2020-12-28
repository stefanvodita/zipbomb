import os
import sys

from zipfile import ZIP_DEFLATED, ZipFile


def zip(path):
    if not os.path.isfile(path):
        print("Only file zipping supported")
        return
    
    with ZipFile(path + ".zip", "w", ZIP_DEFLATED) as zipfile:
        zipfile.write(path)


if __name__ == "__main__":
    zip(sys.argv[1])

