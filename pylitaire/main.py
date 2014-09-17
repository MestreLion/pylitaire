# -*- coding: utf-8 -*-
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

'''Main module and entry point'''

import logging

import pygame

import g
import graphics
import themes
import ui

log = logging.getLogger(__name__)


def main(args=None):
    '''App entry point
        <args> is a list of command line arguments, defaults to sys.argv[1:]
    '''

    g.load_options(args)
    pygame.display.init()
    pygame.font.init()

    themes.init_themes(g.datadirs('themes') + ['/usr/share/aisleriot/cards'])
    graphics.init_graphics()

    gui = ui.Gui()
    gui.run(g.window_size, g.full_screen, g.gamename)

    pygame.quit()
    g.save_options()
