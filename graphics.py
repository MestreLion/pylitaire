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


class Background(object):
    def __init__(self, path="", size=(), color=None, title=""):
        '''Create a new background of <size> from a <path> image file,
            with <color> as a fallback for solid fill. If <path> is empty,
            try to find one using an image named <title> in datadirs.
            <color> defaults to g.BGCOLOR
            <size> defaults to g.window's size
            <title> defaults to g.baize
        '''
        self.path = path or find_image(g.datadirs('images'), title or g.baize)
        self.color = color or g.BGCOLOR
        self.original = None
        self.surface = None

        if size:
            self.resize(size)

    def resize(self, size):
        ''' Creates a background surface of <size> and render the original
            background image to that new surface. If original image is smaller
            than (800, 600) tile (repeat) it, otherwise rescale (stretch/shrink)
        '''
        self.surface = pygame.Surface(size)

        if not self.original and self.path:
            self.original = load_image(self.path).convert()

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


class Slot(object):
    '''Represents a slot image'''

    def __init__(self, path="", size=()):
        self.path = path or find_image(g.datadirs('images'), g.slotname, ['svg'])
        self.original = load_vector(self.path)
        self.surface = None

        if size:
            self.resize(size)

    def resize(self, size=()):
        self.surface = render_vector(self.original, size)


def init_graphics():
    '''Initialize the game window and graphics'''

    log.info("Initializing graphics")

    # Caption, icon and mouse cursor should be set before window is created
    pygame.display.set_caption("Pylitaire")
    pygame.display.set_icon(pygame.image.load(os.path.join(g.DATADIR, 'icons', 'icon-32.png')))

    for cursor in g.cursors.keys():
        g.cursors[cursor] = cursors.load_json(os.path.join(g.DATADIR,
                                                           'cursors', "%s.json" % cursor))
    pygame.mouse.set_cursor(*g.cursors['default'])

    g.background = Background()
    g.slot = Slot()


def resize(size):
    # Set the screen
    flags = pygame.RESIZABLE
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

    g.background.resize(g.window_size)
    g.background.draw()

    # Display the initial window soon as possible, as other elements may take a while
    pygame.display.update()

    playarea = pygame.Rect(g.MARGIN, (g.window_size[0] - g.MARGIN[0],
                                      g.window_size[1] - g.MARGIN[1]))

    return playarea

    # Card height is fixed: 4 cards + margins (top, bottom, 3 between)
    # Card width is free to adjust itself proportionally, according to theme aspect ratio
    # Actual card size is only defined when cards.Deck() renders the theme SVG
    #g.cardsize = (g.window_size[0], (g.window_size[1] - 5 * g.MARGIN[1]) / 4)

    #g.slot.resize(g.cardsize)


def render(spritegroups):
    dirty = []

    for group in spritegroups:
        group.clear(g.window, g.background.surface)
        dirty.extend(group.draw(g.window))

    pygame.display.update(dirty)


def scale_size(original, size=(), proportional=True, multiple=(1, 1)):
    ''' Enlarge or shrink <original> size so it fits a <size>

        If <proportional>, rescaled size will maintain the original width and
        height proportions, so resulting size may be smaller than requested in
        either dimension.

        <multiple> rounds down size to be a multiple of given integers. It
        allow themes to ensure cards have integer size, but may slightly change
        image aspect ratio.

        <original>, <size>, <multiple> and the return value are 2-tuple
        (width, height). Returned width and height are rounded to integers
    '''
    def round_to_multiple(size, multiple):
        return (int(size[0] / multiple[0]) * multiple[0],
                int(size[1] / multiple[1]) * multiple[1])

    if not size or size == original:
        return round_to_multiple(original, multiple)

    if not proportional:
        return round_to_multiple(size, multiple)

    rect = pygame.Rect((0,0), original)
    result = rect.fit(pygame.Rect((0,0), size))
    return round_to_multiple((result.width, result.height), multiple)


def load_image(path, size=(), proportional=True, multiple=(1, 1)):
    ''' Wrapper for pygame.image.load, adding support for SVG images

        See scale_size() for documentation on arguments.

        For regular images, requesting a <size> different than the
        original (after processing aspect, multiple and roundings)
        will use pygame.transform.smoothscale()
    '''
    if os.path.splitext(path.lower())[1] == ".svg":
        return load_svg(path, size, proportional, multiple)

    image = pygame.image.load(path)

    size = scale_size(image.get_size(), size, proportional, multiple)
    if size == image.get_size():
        return image

    # transform.smoothscale() requires a 24 or 32-bit image, so...
    if image.get_bitsize() not in [24, 32]:
        image = image.convert_alpha()

    return pygame.transform.smoothscale(image, size)


def load_svg(path, *scaleargs, **scalekwargs):
    ''' Load an SVG file and return a pygame.image surface
        See scale_size() for documentation on scale arguments.
    '''
    return render_vector(rsvg.Handle(path), *scaleargs, **scalekwargs)


def load_vector(path):
    ''' Load an SVG file from <path> and return a RsvgHandle instance '''
    return rsvg.Handle(path)


def render_vector(svg, *scaleargs, **scalekwargs):
    ''' Render a vector surface, such as the one returned from load_vector(),
        to a pygame surface and return it
    '''

    def bgra_to_rgba(surface):
        ''' Convert a Cairo surface in BGRA format to a RBGA string
            Only needed for little-endian architectures.
        '''
        img = PIL.Image.frombuffer(
            'RGBA', (surface.get_width(), surface.get_height()),
            surface.get_data(), 'raw', 'BGRA', 0, 1)
        return img.tostring('raw', 'RGBA', 0, 1)

    # Calculate size
    svgsize = (svg.props.width, svg.props.height)
    width, height = scale_size(svgsize, *scaleargs, **scalekwargs)

    # If new size is different than original, calculate the scale factor
    scale = (1, 1)
    if not (width, height) == svgsize:
        scale = (float(width)/svgsize[0], float(height)/svgsize[1])

    log.debug("Rendering SVG size (%4g,%4g)->(%4g,%4g): %s",
              svgsize[0], svgsize[1], width, height, svg.props.base_uri)

    # Create a Cairo surface. Architecture endianess determines if cairo surface
    # pixel format will be RGBA or BGRA
    if sys.byteorder == 'little':
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    else:
        dataarray = array.array('c', chr(0) * width * height * 4)
        surface= cairo.ImageSurface.create_for_data(dataarray,
            cairo.FORMAT_ARGB32, width, height, width * 4)

    # Create a context, scale it, and render the SVG
    context = cairo.Context(surface)
    if not scale == (1, 1):
        context.scale(*scale)
    svg.render_cairo(context)

    # Get image data string
    if sys.byteorder == 'little':
        data = bgra_to_rgba(surface)
    else:
        data = dataarray.tostring()

    return pygame.image.frombuffer(data, (width, height), "RGBA").convert_alpha()


def find_image(dirs, title="", exts=()):
    '''Find the first suitable image file in <dirs> and return its full path.
        "Suitable" means being a supported image file, its extension in <exts>,
        and, if <title>, with file title (basename sans extension) matching it.
    '''
    for path in dirs:
        try:
            for basename in os.listdir(path):
                filetitle, ext = os.path.splitext(basename.lower())
                if ((not title or title == filetitle) and
                    (not exts or ext[1:] in exts) and
                    (ext[1:] in IMAGE_EXTS+['svg'])):
                    return os.path.join(path, basename)
        except OSError as e:
            # path not found
            if e.errno == 2:
                continue
            else:
                raise
