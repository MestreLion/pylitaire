# pylitaire - Solitaire in Python
#
#    Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
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

"""Main module and entry point."""

import logging
import os
import sys

# Disable Pygame advertisement
# https://github.com/pygame/pygame/commit/18a31449de93866b369893057f1e60330b53da95
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = ""  # the key just need to exist
import pygame

from . import g
from . import graphics
from . import themes
from . import ui

log = logging.getLogger(__name__)


def main(args=None):
    """App entry point.

    <args> is a list of command line arguments, defaults to sys.argv[1:]
    """

    logging.basicConfig(
        format="[%(levelname)-8s] %(asctime)s %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    g.load_options(args)
    log.debug("Python %s, Pygame %s, SDL %s",
              sys.version.replace('\n', ' '),
              pygame.ver,
              '.'.join(str(_) for _ in pygame.get_sdl_version()))
    # Window position is done by the Window Manager, not Pygame or SDL, but SDL
    # can request a centered window. Must be set before pygame.display.init()
    # Could also use SDL_VIDEO_WINDOW_POS = "x,y"
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.init()
    pygame.font.init()

    graphics.init_graphics()
    themes.init_themes(g.datadirs('themes') + ['/usr/share/aisleriot/cards'])

    gui = ui.Gui()
    gui.run(g.window_size, g.full_screen, g.gamename)

    pygame.quit()
    g.save_options()


def run():
    """Wrapper to main() for graceful exit on KeyboardInterrupt (CTRL+C)"""
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
