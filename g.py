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
#
# Global constants and common functions

import os.path
import xdg.BaseDirectory

'''As a convention, UPPERCASE indicates a constant value, and lowercase is
    for values that may change, either via config file, command-line arguments
    or in-game settings
'''

# General
VERSION = "0.1"
GAMENAME = 'pylitaire'

# Paths
GAMEDIR = os.path.abspath(os.path.dirname(__file__) or '.')
DATADIR = os.path.join(GAMEDIR, 'data')
CONFIGDIR = xdg.BaseDirectory.save_config_path(GAMENAME)

# Graphics
FPS = 30
BGCOLOR = (0, 80, 16)  # Dark green
MARGIN = (20, 10)  # window margins for the playarea, in pixels
window = None  # surface created by pygame.dsplay.set_mode()
background = None  # graphics.Background
slot = None  # graphics.Slot
playarea = None  # pygame.Rect
cardsize = ()  # (width, height) of current card size
cursors = {'default': None,
           'drag': None,
           'draggable': None,
           }

# Options
fullscreen = False
window_size = (1300, 900)
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
