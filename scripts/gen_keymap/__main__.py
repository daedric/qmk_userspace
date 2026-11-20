import argparse

from codegen import generate
from ergol import HOSTS
from keymaps import KEYMAPS

parser = argparse.ArgumentParser(description="Process keymap options.")
parser.add_argument(
    "--keymap",
    choices=list(KEYMAPS),
    default="std",
    help="Specify the keymap to use.",
)
parser.add_argument(
    "--host",
    choices=list(HOSTS),
    default="us",
    help="Specify the host on which the keyboard will be plugged",
)
parser.add_argument(
    "--autoshift",
    action="store_true",
    default=False,
    help="Autoshift support",
)

args = parser.parse_args()
print(generate(KEYMAPS[args.keymap], HOSTS[args.host], args.autoshift))
