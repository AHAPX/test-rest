import argparse

from loaders import get_loader


parser = argparse.ArgumentParser(description='Test-REST')
parser.add_argument('filename', type=str, help='test cases file')
parser.add_argument('--format', '-f', type=str, help='file format, default = yaml')
args = parser.parse_args()


if args.format:
    loader = get_loader(args.format)
else:
    loader = get_loader(args.filename.split('.')[-1])
if not loader:
    raise ValueError('format is not defined')

actions = loader(args.filename).load()
actions.run()
