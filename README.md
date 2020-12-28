# zipbomb

This project is inspired by David Fifield's paper, "A better zipbomb" (https://www.usenix.org/conference/woot19/presentation/fifield).

## Files

### bombify.py
Take an unassuming zip file and turn it into a zipbomb using the overlapped files strategy.

The provided zip file is expected to contain a single file, but the bombification process should work as long as the first file header correspons to the first central directory header.

For ease of implementation, I assumed the filename is only one byte, and there are no comments or extra fields. This allows the file header and central directory header sizes to be known.

### unzip.py
Unzip a zip file recursivelly, i.e. any zip files found inside the initial one, will be unzipped too.

### zip.py
Zip a file in the most basic manner, to avoid comments and extra fields added by common zipping tools.

### notes
Explanation of zipfile contents and 2 examples of zipfiles split into their corresponding records.
The purpose of this analysis is to figure out which header fields can be reused from a file previously found in the zipfile and which fields should be modified.

Zipfiles analysed here were produced with David Fifield's zipbomb script.
