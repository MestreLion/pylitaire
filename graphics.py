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
# Graphics-related functions


import os
import logging

import pygame

import g

log = logging.getLogger(__name__)


def init_graphics():
    ''' Initialize the game window and graphics '''

    log.info("Initializing graphics")

    # Set caption and icon
    pygame.display.set_caption("Pylitaire")
    pygame.display.set_icon(pygame.image.load(os.path.join(g.DATADIR, 'icons', 'icon-48.png')))

    # Set the screen
    flags = 0
    size = g.window_size
    if g.fullscreen:
        log.debug("Setting fullscreen, desktop resolution (%s, %s)",
                  pygame.display.Info().current_w,
                  pygame.display.Info().current_h)
        flags |= pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        size = (0, 0)  # use current desktop resolution
    else:
        log.debug("Setting window size %s", size)
    g.window = pygame.display.set_mode(size, flags)
    g.window_size = g.window.get_size()

    # Set the background
    g.background = pygame.Surface(g.window.get_size())
    g.background.fill(g.BGCOLOR)
    g.window.blit(g.background, (0, 0))
    pygame.display.update()


def render(sprites, clear=False):
    sprites.clear(g.window, g.background)
    if clear:
        g.window.blit(g.background, (0, 0))
    dirty = sprites.draw(g.window)
    pygame.display.update(dirty)
