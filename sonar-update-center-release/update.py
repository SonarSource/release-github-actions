import argparse
import sys

# The entire file was written by AI.

PUBLIC_VERSION = 'publicVersions='


def main():
    parser = argparse.ArgumentParser(
        description='Update a .properties file with a new version entry.'
    )
    parser.add_argument('--file', required=True, help='Input .properties file')
    parser.add_argument('--version', required=True, help='New version string (e.g. 5.5.0.6356)')
    parser.add_argument('--description', required=True, help='Release description')
    parser.add_argument('--date', required=True, help='Release date (YYYY-MM-DD)')
    parser.add_argument('--changelogUrl', required=True, help='Changelog URL')
    parser.add_argument('--downloadUrl', required=True, help='Download URL')
    args = parser.parse_args()

    # First pass: find the current publicVersions value to move it to archivedVersions
    old_public_version = None
    with open(args.file, 'r') as f:
        for line in f:
            if line.startswith(PUBLIC_VERSION):
                old_public_version = line.rstrip('\n')[len(PUBLIC_VERSION):]
                break

    if old_public_version is None:
        print('ERROR: publicVersions not found in input file', file=sys.stderr)
        sys.exit(1)

    # Second pass: build the output
    with open(args.file, 'r') as f:
        lines = f.readlines()

    output_lines = []
    insert_block_after_next_blank = False

    for line in lines:
        stripped = line.rstrip('\n')

        if stripped.startswith('archivedVersions='):
            output_lines.append(f'{stripped},{old_public_version}\n')
            continue

        if stripped.startswith(PUBLIC_VERSION):
            output_lines.append(f'{PUBLIC_VERSION}{args.version}\n')
            insert_block_after_next_blank = True
            continue

        if insert_block_after_next_blank and stripped == '':
            output_lines.append(line)
            v = args.version
            output_lines.append(f'{v}.description={args.description}\n')
            output_lines.append(f'{v}.date={args.date}\n')
            output_lines.append(f'{v}.changelogUrl={args.changelogUrl}\n')
            output_lines.append(f'{v}.downloadUrl={args.downloadUrl}\n')
            output_lines.append('\n')
            insert_block_after_next_blank = False
            continue

        output_lines.append(line)

    with open(args.file, 'w') as f:
        f.writelines(output_lines)

    print(f'Written {args.file}', file=sys.stderr)


if __name__ == '__main__':
    main()
