#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
#
# Main module and entry point for Pylitaire

import sys
import logging

import pygame

import g
import graphics
import themes
import ui

log = logging.getLogger(__name__)


def main(*argv):
    '''Main Program, <argv> as a list of command line arguments'''

    g.load_options(*argv)

    pygame.display.init()
    pygame.font.init()
    display_size = graphics.init_graphics(g.window_size, g.full_screen)
    themes.init_themes()

    gui = ui.Gui(display_size)
    gui.load_game(g.gamename)

    clock = pygame.time.Clock()
    run = True
    while run:
        run = gui.handle_events()
        gui.update()
        graphics.render(gui.spritegroups, gui.clear)
        gui.clear = False

        if g.profile:
            if pygame.time.get_ticks() > 10000:
                return True

        clock.tick(g.FPS)

    g.save_options()
    pygame.quit()
    return True




if __name__ == "__main__":
    logging.basicConfig()
    log = logging.getLogger(g.GAMENAME)
    try:
        sys.exit(0 if main(*sys.argv[1:]) else 1)
    except KeyboardInterrupt:
        pass
