# -*- coding: utf-8 -*-
#
#    Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#    This file is part of Pylitaire game
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>

'''Global constants, paths, singletons and game options

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
'''

import os.path
import xdg.BaseDirectory


# General
VERSION = "0.5"
GAMENAME = 'pylitaire'

# Paths
GAMEDIR = os.path.abspath(os.path.dirname(__file__) or '.')
DATADIR = os.path.join(GAMEDIR, 'data')
CONFIGDIR = xdg.BaseDirectory.save_config_path(GAMENAME)

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
