import sys
from argparse import ArgumentParser

from polaris.user import main as u_main
from polaris.media import main as m_main
from polaris.utils import set_temp, set_verbose

MAIN_MAP = {
    "user": u_main,
    "media": m_main,
}

parser = ArgumentParser("polaris")
parser.add_argument("action", choices=MAIN_MAP.keys(), help="What the provided link is about")
parser.add_argument("link", help="The link to the instagram page")

parser.add_argument("-o", "--output", default="./out/", help="output directory to download media")
parser.add_argument("-t", "--temp", default="./tmp/", help="temp directory to store temp files")

parser.add_argument("-v", "--verbose", action="store_true", default=False, help="increse verbosity")

args = parser.parse_args()

set_verbose(args.verbose)
set_temp(args.temp)
sys.exit(MAIN_MAP[args.action](args.link, args.output))
