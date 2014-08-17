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
import math

import pygame

import g

log = logging.getLogger(__name__)

# File extensions of pygame supported image formats
# As documented in http://www.pygame.org/docs/ref/image.html
IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'pcx', 'tga', 'tif', 'tiff',
              'lbm', 'pbm', 'pbm', 'pgm', 'ppm', 'xpm']


class Background():
    def __init__(self, path="", size=(), color=None, title=""):
        ''' Create a new background of <size> from a <path> image file,
            with <color> as a fallback for solid fill. If <path> is empty,
            try to find one using find_background_file(<title>).
            <color> defaults to g.BGCOLOR
            <size> defaults to g.window's size
        '''
        self.path = path or self.find_background_file()
        if self.path:
            self.original = pygame.image.load(self.path).convert()
        else:
            self.original = None
        self.color = color or g.BGCOLOR
        self.resize(size or g.window.get_size())

    def resize(self, size):
        ''' Creates a background surface of <size> and render the original
            background image to that new surface. If original image is smaller
            than (800, 600) tile (repeat) it, otherwise rescale (stretch/shrink)
        '''
        self.surface = pygame.Surface(size)

        if not self.original:
            # No suitable background file found. Use a solid color fill
            self.surface.fill(self.color)
            return

        bgw, bgh = self.original.get_size()

        if bgw >= 800 and bgh >= 600:
            # Scale
            pygame.transform.smoothscale(self.original, size, self.surface)
        else:
            # Tile
            for i in xrange(int(math.ceil(float(size[0]) / bgw))):
                for j in xrange(int(math.ceil(float(size[1]) / bgh))):
                    self.surface.blit(self.original, (i * bgw, j * bgh))

    def draw(self, destsurface=None, position=()):
        ''' Draw the background to a destination surface, defaults to g.window,
            at the specified position, defaults to (0, 0)
        '''
        surface = destsurface or g.window
        surface.blit(self.surface, position or (0, 0))

    @classmethod
    def find_background_file(cls, title=""):
        ''' Find a suitable background file in config and data dirs, return
            its full path. "Suitable" means being a supported image file with
            title (basename sans extension) matching <title>
            <title> defaults to g.baize
        '''
        title = title or g.baize
        for path in [os.path.join(g.CONFIGDIR, 'images'),
                     os.path.join(g.DATADIR, 'images')]:
            try:
                for basename in os.listdir(path):
                    filetitle, ext = os.path.splitext(basename.lower())
                    if filetitle == title and ext[1:] in IMAGE_EXTS:
                        return os.path.join(path, basename)
            except OSError as e:
                # path not found
                if e.errno == 2:
                    continue
                else:
                    raise


def init_graphics():
    ''' Initialize the game window and graphics '''

    log.info("Initializing graphics")

    # Set caption and icon
    pygame.display.set_caption("Pylitaire")
    pygame.display.set_icon(pygame.image.load(os.path.join(g.DATADIR, 'icons', 'icon-32.png')))

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
    g.background = Background()
    g.background.draw()

    # Display the initial window
    pygame.display.update()


def render(sprites, clear=False):
    sprites.clear(g.window, g.background.surface)
    if clear:
        g.background.draw()
    dirty = sprites.draw(g.window)
    pygame.display.update(dirty)
