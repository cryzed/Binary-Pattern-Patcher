import os
import re
import sys
import json
import mmap
import tempfile


BUFFER_SIZE = 134217728  # 128 MB
OPTIONS = {
    'replace_pattern': True,
    'keep_size': False
}


def hex_csv_to_bin(string):
    return ''.join(chr(int(token.strip(), 16)) for token in string.split(','))


def main(patch_path, file_path):
    print '- Patching', file_path, '...'
    with open(patch_path) as file:
        patches = json.load(file)

    file = open(file_path, 'r+')
    data = mmap.mmap(file.fileno(), 0)

    output = tempfile.NamedTemporaryFile(delete=False)
    for patch in patches:
        print '  -', patch['name']
        options = {}
        options.update(OPTIONS)
        if 'options' in patch:
            options.update(patch['options'])

        # TODO: Possibly needs fix for patch file with multiple patterns
        for match in re.finditer(patch['pattern'], data, re.DOTALL):
            print '    - Found match at %d - %d (%d bytes)' % (match.start(), match.end(), match.end()-match.start())
            while data.tell() < match.start():
                distance = match.start() - data.tell()
                size = min(distance, BUFFER_SIZE)
                chunk = data.read(size)
                output.write(chunk)

            if not options['replace_pattern']:
                distance = match.end() - data.tell()
                output.write(data.read(distance))

            patch_data = hex_csv_to_bin(patch['data'])
            output.write(patch_data)

            if options['keep_size']:
                data.seek(len(patch_data), 1)
            else:
                data.seek(match.end())

        print
        chunk = data.read(BUFFER_SIZE)
        while chunk:
            output.write(chunk)
            chunk = data.read(BUFFER_SIZE)

    output.close()
    os.remove(file_path)
    os.rename(output.name, file_path)


if __name__ == '__main__':
    if len(sys.argv[1:]) < 2:
        print 'Usage: %s [PATCH] [FILE]...' % sys.argv[0]
        print 'Patch given files with the specified patch file.'
        sys.exit(1)
    for file_path in sys.argv[2:]:
        main(sys.argv[1], file_path)
