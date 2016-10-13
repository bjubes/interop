#!/usr/bin/env python
# CLI for interacting with interop server.

from __future__ import print_function
import argparse
import datetime
import getpass
import logging
import pprint
import sys
import time

from interop import Client
from interop import Target
from interop import Telemetry
from upload_targets import upload_targets, upload_legacy_targets


def missions(args, client):
    missions = client.get_missions()
    for m in missions:
        pprint.pprint(m.serialize())


def targets(args, client):
    if args.legacy_filepath:
        upload_legacy_targets(client, args.legacy_filepath, args.target_dir)
    else:
        upload_targets(client, args.target_dir)


def probe(args, client):
    while True:
        start_time = datetime.datetime.now()

        telemetry = Telemetry(0, 0, 0, 0)
        telemetry_resp = client.post_telemetry(telemetry)
        obstacle_resp = client.get_obstacles()

        end_time = datetime.datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        logging.info('Executed interop. Total latency: %f', elapsed_time)

        delay_time = args.interop_time - elapsed_time
        if delay_time > 0:
            try:
                time.sleep(delay_time)
            except KeyboardInterrupt:
                sys.exit(0)


def main():
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout,
        format='%(asctime)s: %(name)s: %(levelname)s: %(message)s')

    # Parse command line args.
    parser = argparse.ArgumentParser(description='AUVSI SUAS Interop CLI.')
    parser.add_argument('--url',
                        required=True,
                        help='URL for interoperability.')
    parser.add_argument('--username',
                        required=True,
                        help='Username for interoperability.')
    parser.add_argument('--password', help='Password for interoperability.')
    subparsers = parser.add_subparsers(help='Sub-command help.')

    subparser = subparsers.add_parser('missions', help='Get missions.')
    subparser.set_defaults(func=missions)

    subparser = subparsers.add_parser(
        'targets',
        help='Upload targets.',
        description='''Upload targets to the interoperability server.

This tool searches for target JSON and images files within --target_dir
conforming to the 2017 Object File Format and uploads the target
characteristics and thumbnails to the interoperability server.

Alternatively, if --legacy_filepath is specified, that file is parsed as the
legacy 2016 tab-delimited target file format. Image paths referenced in the
file are relative to --target_dir.

There is no deduplication logic. Targets will be uploaded multiple times, as
unique targets, if the tool is run multiple times.''',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser.set_defaults(func=targets)
    subparser.add_argument(
        '--legacy_filepath',
        help='Target file in the legacy 2016 tab-delimited format.')
    subparser.add_argument('--target_dir',
                           required=True,
                           help='Directory containing target data.')

    subparser = subparsers.add_parser('probe', help='Send dummy requests.')
    subparser.set_defaults(func=probe)
    subparser.add_argument('--interop_time',
                           type=float,
                           default=1.0,
                           help='Time between sent requests (sec).')

    # Parse args, get password if not provided.
    args = parser.parse_args()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass('Interoperability Password: ')

    # Create client and dispatch subcommand.
    client = Client(args.url, args.username, password)
    args.func(args, client)


if __name__ == '__main__':
    main()
