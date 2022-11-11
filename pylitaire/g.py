# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Global constants, paths, singletons and game options.

Globals are basically divided in 4 groups:

- Constants:
    In UPPERCASE. Most are used only once, but they are better here than hardcoded in
    some module, like the game FPS and or status bar height. All immutable and literal.

- Paths:
    Defined here and set only once, so also in UPPERCASE.

- Singletons:
    Objects that are used and set in different places, like the background surface,
    and for now it's convenient to have them here instead of passing  as arguments
    everywhere. All are initialized here as None.

    Legitimate candidates for this group are lists/dicts such as the themes, cursors
    and games rules found after their respective init(). But apart from those this group
    should be kept as a minimum, and in an ideal world this group would not even exist.

- Options:
    The group that gives this module a good and fair reason to exist. Options are read
    from command line, config file, and may be changed in-game. They can also be saved back
    to config file before exiting. Values hardcoded here are just the "factory defaults"

This module can be renamed as 'options' if the word 'Global' is so frowned upon.
"""

import configparser
import json
import logging
import os.path
import shutil
import sys
import time
import typing as t

import xdg.BaseDirectory

if t.TYPE_CHECKING:
    from . import graphics
    from . import cursors as cursors_

log = logging.getLogger(__name__)
start_time = time.time()  # for profiling

# General
VERSION = "1.0"
APPNAME = 'pylitaire'

# Paths
GAMEDIR = os.path.abspath(os.path.dirname(__file__) or '.')
DATADIR = os.path.join(GAMEDIR, 'data')
CONFIGDIR = xdg.BaseDirectory.save_config_path(APPNAME)
WINDOWFILE = os.path.join(CONFIGDIR, 'window.json')
CONFIGFILE = os.path.join(CONFIGDIR, '{}.conf'.format(APPNAME))

# Graphics
FPS = 30
BGCOLOR = (0, 80, 16)  # Dark green
MARGIN = (20, 10)  # Board margin and minimum card padding
SBHEIGHT = 25  # status bar height
SBCOLOR = (242, 241, 240)  # status bar background color
MIN_SIZE = (320, 192)  # Minimum windows size

background: t.Optional['graphics.Background'] = None
slot:       t.Optional['graphics.Slot']       = None
cursors:    t.Dict[str, t.Optional['cursors_.Cursor']] = {
    'default': None,
    'drag': None,
    'draggable': None,
}

# Options
# Actual defaults are at config/config.template.ini
full_screen = False
window_size = (960, 640)
debug = False
profile = False
baize = "baize-ubuntu"
theme = "life_and_smooth"
slotname = "slot-gnome"
doubleclicklimit = 400
gamename = "klondike"


def datadirs(dirname):
    """List of game relevant data directories.

    Useful for finding data files such as themes and images.
    """
    return [os.path.join(CONFIGDIR, dirname),
            os.path.join(DATADIR, dirname)]


def load_options(args):
    """Load all global options from config file and command line arguments."""
    global window_size, full_screen, debug, profile
    global baize, theme, slotname, gamename, doubleclicklimit

    # Too lazy for argparse right now
    if args is None:
        args = sys.argv[1:]
    # pre-read debug to configure logging sooner
    if "--debug" in args:
        logging.getLogger(__package__).setLevel(logging.DEBUG)
    log.debug(args)

    options: t.Dict[str, t.Dict[str, t.Any]] = {'options': dict(
        full_screen=full_screen,
        window_size=window_size,
        debug=debug,
        profile=profile,
        baize=baize,
        theme=theme,
        slotname=slotname,
        doubleclicklimit=doubleclicklimit,
        gamename=gamename,
    )}
    try:
        read_config(CONFIGFILE, options)
    except (IOError, ValueError) as e:
        log.warning("Error reading config: %s", e)

    # Override options with command-line arguments
    if "--fullscreen" in args: full_screen = True
    if "--debug"      in args: debug       = True
    if "--profile"    in args: profile     = True

    # Set the log level
    loglevel = None
    if profile: loglevel = logging.INFO
    if debug:   loglevel = logging.DEBUG
    if loglevel:
        logging.getLogger(__package__).setLevel(loglevel)

    log.debug(options)
    baize            = options["options"]["baize"]
    theme            = options["options"]["theme"]
    slotname         = options["options"]["slotname"]
    doubleclicklimit = options["options"]["doubleclicklimit"]
    gamename         = options["options"]["gamename"]

    try:
        log.debug("Loading window size from: %s", WINDOWFILE)
        with open(WINDOWFILE) as fp:
            # Read in 2 steps to guarantee a valid (w, h) numeric 2-tuple
            width, height = json.load(fp)
            window_size = (int(width),
                           int(height))
    except (IOError, ValueError) as e:
        log.warning("Error reading window size, using factory default: %s", e)


def save_options():
    try:
        log.debug("Saving window size to: %s", WINDOWFILE)
        with open(WINDOWFILE, 'w') as fp:
            json.dump(window_size, fp)
    except IOError as e:
        log.warning("Could not write window size: %s", e)


def read_config(path, options):
    cp = configparser.ConfigParser()

    log.debug("Loading config from: %s", CONFIGFILE)
    if not cp.read(path, encoding='utf-8'):
        # Config file does not exist, create one from template and read again
        log.info("Config not found, creating one and using default values: %s", path)
        shutil.copyfile(os.path.join(DATADIR, 'config', 'config.template.ini'), path)
        cp.read(path, encoding='utf-8')

    def get_iter(s, o):
        return (_.strip() for _ in cp.get(s, o).split(','))

    def get_list(s, o):
        return list(get_iter(s, o))

    def get_tuple(s, o):
        return tuple(get_iter(s, o))

    # .keys() to avoid 'RuntimeError: dictionary changed size during iteration'
    for section in options.keys():
        if not cp.has_section(section):
            log.warning("Section [%s] not found in %s", section, path)
            continue

        # For other sections options list is taken from options dict
        for opt in options[section]:
            if   isinstance(options[section][opt], bool):  get = cp.getboolean
            elif isinstance(options[section][opt], int):   get = cp.getint
            elif isinstance(options[section][opt], float): get = cp.getfloat
            elif isinstance(options[section][opt], list):  get = get_list
            elif isinstance(options[section][opt], tuple): get = get_tuple
            else:                                          get = cp.get

            try:
                options[section][opt] = get(section, opt)

            except configparser.NoOptionError as e:
                log.warning("%s in %s", e, path)

            except ValueError as e:
                log.warning("%s in '%s' option of %s", e, opt, path)


def runtime(start=0):
    if not start:
        start = start_time
    return "{:.0f}".format(1000 * (time.time() - start))
