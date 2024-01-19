#!/usr/bin/env python

import argparse
import datetime
from io_interface import CliIO
from socratic_dialogue import CliSocraticDialogueRoom

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--log-dir', type=str, help="Directory to write logs to")
    parser.add_argument('--survey-config', type=str, help="Config file for post-dialogue survey")
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    io_handler = CliIO()
    sd_room = CliSocraticDialogueRoom(io_handler, verbose=args.verbose)
    sd_room.run_room()

    if args.log_dir:
        sd_room.record(args.log_dir, timestamp)

if __name__ == '__main__':
    main()