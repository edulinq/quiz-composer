import sys

import edq.clilib.list

def main() -> int:
    """ List this CLI dir. """

    return edq.clilib.list.main()

if (__name__ == '__main__'):
    sys.exit(main())
