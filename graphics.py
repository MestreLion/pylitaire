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
import sys
import logging
import math
import array

import pygame
import rsvg
import cairo
import PIL.Image

import g
import cursors

log = logging.getLogger(__name__)

# File extensions of pygame supported image formats
# As documented at http://www.pygame.org/docs/ref/image.html
IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'pcx', 'tga', 'tif', 'tiff',
              'lbm', 'pbm', 'pgm', 'ppm', 'xpm']


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
            self.original = load_image(self.path).convert()
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

    # Set the cursors
    for cursor in g.cursors.keys():
        g.cursors[cursor] = cursors.load_json(os.path.join(g.DATADIR,
                                                           'cursors', "%s.json" % cursor))
    pygame.mouse.set_cursor(*g.cursors['default'])

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


def render(spritegroups, clear=False):
    dirty = []
    if clear:
        g.background.draw()

    for group in spritegroups:
        group.clear(g.window, g.background.surface)
        dirty.extend(group.draw(g.window))

    if clear:
        dirty = [g.window.rect()]

    pygame.display.update(dirty)


def scale_keep_aspect(size, maxsize):
    ''' Enlarge or shrink <size> so it fits <maxsize>, keeping its proportions
        <size>, <maxsize> and return value are 2-tuple (width, height)
    '''
    original = pygame.Rect((0,0), size)
    result = original.fit(pygame.Rect((0,0), maxsize))
    return result.width, result.height


def load_image(path, size=(), keep_aspect=True):
    ''' Wrapper for pygame.image.load, adding support for SVG images
        If <keep_aspect> is True, rescaled images will maintain the original
        width and height proportions. For regular images, requesting a <size>
        will use pygame.transform.smoothscale()
    '''
    if os.path.splitext(path.lower())[1] == ".svg":
        return load_svg(path, size, keep_aspect)

    image = pygame.image.load(path)
    if not size or size == image.get_size():
        return image

    if keep_aspect:
            size = scale_keep_aspect(image.get_size(), size)

    return pygame.transform.smoothscale(image, size)


def load_svg(path, size=(), keep_aspect=True):
    ''' Load an SVG file and return a pygame.image surface with the specified size
        - size: a (width, height) tuple. If None, uses the SVG declared size
        - keep_aspect: if scaling should keep original width and height proportions,
          but resulting size may be smaller than requested in either width or height
    '''

    def bgra_to_rgba(surface):
        ''' Convert a Cairo surface in BGRA format to a RBGA string
            Only needed for little-endian architectures.
        '''
        img = PIL.Image.frombuffer(
            'RGBA', (surface.get_width(), surface.get_height()),
            surface.get_data(), 'raw', 'BGRA', 0, 1)
        return img.tostring('raw', 'RGBA', 0, 1)

    # Load the SVG
    svg = rsvg.Handle(path)

    # Calculate new size based on original size, requested size, and aspect ratio
    svgsize = (svg.props.width, svg.props.height)
    if size:
        if keep_aspect:
            width, height = scale_keep_aspect(svgsize, size)
        else:
            width, height = size
    else:
        width, height = svgsize

    # Make sure size is a multiple of (13, 5), so all cards have integer sizes
    width, height = int(width / 13) * 13, int(height / 5) * 5

    # If a size was requested, calculate the scale factor
    scale = size and (float(width)/svgsize[0], float(height)/svgsize[1])

    log.debug("Loading SVG size (%4g,%4g)->(%4g,%4g): %s",
              svgsize[0], svgsize[1], width, height, path)

    # Create a Cairo surface. Archtecture endianess determines if cairo surface
    # pixel format will be RGBA or BGRA
    if sys.byteorder == 'little':
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    else:
        dataarray = array.array('c', chr(0) * width * height * 4)
        surface= cairo.ImageSurface.create_for_data(dataarray,
            cairo.FORMAT_ARGB32, width, height, width * 4)

    # Create a context, scale it, and render the SVG
    context = cairo.Context(surface)
    if scale:
        context.scale(*scale)
    svg.render_cairo(context)

    # Get image data string
    if sys.byteorder == 'little':
        data = bgra_to_rgba(surface)
    else:
        data = dataarray.tostring()

    return pygame.image.frombuffer(data, (width, height), "RGBA").convert_alpha()
