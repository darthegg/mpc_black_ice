#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

import argparse
import logging

from src.agent import Agent


def main():
    argparser = argparse.ArgumentParser(description="CARLA Manual Control Client")
    argparser.add_argument("-v", "--verbose", action="store_true", dest="debug", help="print debug information")
    argparser.add_argument(
        "--host", metavar="H", default="127.0.0.1", help="IP of the host server (default: 127.0.0.1)"
    )
    argparser.add_argument(
        "-p", "--port", metavar="P", default=2000, type=int, help="TCP port to listen to (default: 2000)"
    )
    argparser.add_argument("-a", "--autopilot", action="store_true", help="enable autopilot")
    argparser.add_argument(
        "--res", metavar="WIDTHxHEIGHT", default="1280x720", help="window resolution (default: 1280x720)"
    )
    argparser.add_argument(
        "--filter", metavar="PATTERN", default="vehicle.*", help='actor filter (default: "vehicle.*")'
    )
    argparser.add_argument("--rolename", metavar="NAME", default="hero", help='actor role name (default: "hero")')
    argparser.add_argument("--gamma", default=2.2, type=float, help="Gamma correction of the camera (default: 2.2)")
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split("x")]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)
    logging.info("listening to server %s:%s", args.host, args.port)

    agent = Agent(args)

    try:
        agent.run()

    except KeyboardInterrupt:
        print("\nCancelled by user. Bye!")


if __name__ == "__main__":

    main()
