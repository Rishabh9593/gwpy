#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) Joseph Areeda (2015-2019)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""Generate plots of GW observatory data using GWpy
"""

import time

import os
import sys
from importlib import import_module
from argparse import (ArgumentParser, ArgumentDefaultsHelpFormatter)

from matplotlib import use

from .. import __version__
from . import PRODUCTS

__author__ = 'Joseph Areeda <joseph.areeda@ligo.org>'

# if launched from a terminal with no display
# Must be done before modules like pyplot are imported
if len(os.getenv('DISPLAY', '')) == 0:
    use('Agg')

PROG_START = time.time()    # verbose enough times major ops

INTERACTIVE = hasattr(sys, 'ps1')


# -- init command line --------------------------------------------------------

class _ArgumentParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(_ArgumentParser, self).__init__(*args, **kwargs)
        self._positionals.title = 'Positional arguments'
        self._optionals.title = 'Help options'


def create_parser():
    parser = _ArgumentParser(
        description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)

    # set the argument parser to act as the parent
    parentparser = _ArgumentParser(add_help=False)
    parentparser._optionals.title = 'Verbosity options'
    parentparser.add_argument('-v', '--verbose', action='count', default=1,
                              help='increase verbose output')
    parentparser.add_argument('-s', '--silent', action='store_true',
                              help='show only fatal errors')

    # subparsers are dependent on which action is chosen
    subparsers = parser.add_subparsers(
        dest='mode', title='Actions',
        description='Select one of the following actions:')

    # Add the subparsers for each plot product
    for product, product_class in PRODUCTS.items():
        subparser = subparsers.add_parser(
            product, help=product_class.__doc__.strip().split('\n')[0],
            parents=[parentparser],
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        product_class.init_cli(subparser)

    return parser


def parse_command_line(args=None):
    parser = create_parser()
    return parser.parse_args(args=args)


# -- run ----------------------------------------------------------------------

def main(args=None):
    """Run gwpy-plot

    Returns the relevant exit code, that can be passed to :func:`sys.exit`.
    """
    # parse the command line and create a product object
    args = parse_command_line(args=args)
    prod = PRODUCT[args.mode](args)
    prod.log(2, ('{0} created'.format(prod.action)))

    # log how long it took us to get here
    setup_time = time.time() - PROG_START
    prod.log(2, 'Setup time %.1f sec' % setup_time)

    # -- generate the plot
    prod.run()

    # overload the current namespace for interactive (i)python users
    if INTERACTIVE:
        # import pyplot so that user has access to it
        from matplotlib import pyplot as plt  # pylint: disable=unused-import
        plot = prod.plot
        # pull raw data and plotted results from product for their use
        timeseries = prod.timeseries
        result = prod.result
        print('Raw data is in "timeseries", plotted data is in "result"')
        ax = plot.gca()

    run_time = time.time() - PROG_START
    prod.log(1, 'Program run time: %.1f' % run_time)
    if prod.got_error:
        return 2     # make sure when running batch they can test for error
