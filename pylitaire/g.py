# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Global constants, paths, singletons and game options

Globals are basically divided in 4 groups:

- Constants
    In UPPERCASE. Most are used only once, but they are better here than
    hardcoded in some module, like the game FPS and or status bar height
    All immutable and literal.

- Paths
    Defined here and set only once, so also in UPPERCASE

- Singletons
    For objects that are used and set in different places, like the background
    surface, and for now it's convenient to have them here instead of passing
    as arguments everywhere. All are initialized here as None.

    Legitimate candidates for this group are lists/dicts such as the themes,
    cursors and games rules found after their respective init(). But apart
    from those this group should be kept as a minimum

    ... and in an ideal world this group would not even exist.

- Options
    The group that gives this module a good and fair reason to exist. Options
    are read from command line, config file, and may be changed in-game. They
    can also be saved back to config file before exiting. Values hardcoded
    here are just the "factory defaults"

This module can be renamed as 'options' if the word 'Global' scares you.
"""

import sys
import os.path
import xdg.BaseDirectory
import json
import logging


log = logging.getLogger(__name__)

# General
VERSION = "0.9"
APPNAME = 'pylitaire'

# Paths
GAMEDIR = os.path.abspath(os.path.dirname(__file__) or '.')
DATADIR = os.path.join(GAMEDIR, 'data')
CONFIGDIR = xdg.BaseDirectory.save_config_path(APPNAME)
WINDOWFILE = os.path.join(CONFIGDIR, 'window.json')

# Graphics
FPS = 30
BGCOLOR = (0, 80, 16)  # Dark green
MARGIN = (20, 10)  # Board margin and minimum card padding
SBHEIGHT = 25  # status bar height
SBCOLOR = (242, 241, 240)  # status bar background color

background = None  # graphics.Background
slot = None  # graphics.Slot
cursors = {'default': None,
           'drag': None,
           'draggable': None,
           }

# Options
full_screen = False
window_size = (960, 640)
debug = False
profile = False
baize = "baize-ubuntu"
theme = "life_and_smooth"
slotname = "slot-gnome"
doubleclicklimit = 400
gamename = "pylitaire"


def datadirs(dirname):
    '''Return a list of game relevant data directories, useful for finding data
        files such as themes and images
    '''
    return [os.path.join(CONFIGDIR, dirname),
            os.path.join(DATADIR, dirname)]

def load_options(args):
    '''Load all global options from config file and command line arguments'''
    global window_size, full_screen, debug, profile

    # Too lazy for argparse right now
    if args is None:
        args = sys.argv[1:]
    if "--fullscreen" in args: full_screen = True
    if "--debug"      in args: debug       = True
    if "--profile"    in args: profile     = True

    if debug:
        logging.getLogger(__package__).setLevel(logging.DEBUG)

    try:
        log.debug("Loading window size from: %s", WINDOWFILE)
        with open(WINDOWFILE) as fp:
            # Read in 2 steps to guarantee a valid (w, h) numeric 2-tuple
            width, height = json.load(fp)
            window_size = (int(width),
                           int(height))
    except (IOError, ValueError) as e:
        log.warn("Error reading window size, using factory default: %s", e)

def save_options():
    try:
        log.debug("Saving window size to: %s", WINDOWFILE)
        with open(WINDOWFILE, 'w') as fp:
            json.dump(window_size, fp)
    except IOError as e:
        log.warn("Could not write window size: %s", e)
