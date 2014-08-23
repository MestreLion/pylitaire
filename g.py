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


class Enum(object):
    ''' A basic implementation of Enums in Python '''

    @classmethod
    def name(cls, value):
        ''' Quick-and-dirty fallback for getting the "name" of an enum item
            Enums can customize the name by overwriting this method
        '''

        # value as string, if it matches an enum attribute.
        # Allows short usage as Enum.name("VALUE") besides Enum.name(Enum.VALUE)
        if hasattr(cls, str(value)):
            return cls.name(getattr(cls, value, None))

        # value not handled in subclass name()
        for k, v in cls.__dict__.items():
            if v == value:
                return k.replace('_', ' ').title()

        # value not found
        raise KeyError("Value '%s' not found in enum '%s'" %
                       (value, cls.__name__))

    class _meta(type):
        def __iter__(self):  # "self" for a metaclass refers to classes, not instances
            for name, value in sorted(self.__dict__.items(), key=lambda _: _[1]):
                if (not name.startswith("_") and
                    not name in ['name'] + getattr(self, '__non_members__', [])):
                    yield value
    __metaclass__ = _meta


def datadirs(dirname):
    '''Return a list of game relevant data directories, useful for finding data
        files such as themes as images
    '''
    return [os.path.join(CONFIGDIR, dirname),
            os.path.join(DATADIR, dirname)]
