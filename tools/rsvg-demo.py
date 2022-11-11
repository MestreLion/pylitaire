#!/usr/bin/env python3
# This file is part of Pylitaire
# Copyright (C) 2022 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""
LibRsvg + Pycairo (+ PIL) loading demo
See https://stackoverflow.com/a/74401182/624066
"""
import os.path as osp
import sys

import cairo
import gi
import PIL.Image
import pygame
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

WIDTH = 1200
HEIGHT = 720

PATH = osp.join(osp.dirname(__file__), '../pylitaire/data/themes/ubuntu_bonded.svg')
if len(sys.argv) > 1:
    PATH = sys.argv[1]


def load_svg(path: str, size: tuple) -> pygame.Surface:
    """Render an SVG file to a new pygame surface and return that surface."""
    # Load the SVG file
    svg = Rsvg.Handle.new_from_file(path)

    # Create a Cairo surface.
    # Nominally ARGB, but in little-endian architectures it is effectively BGRA
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *size)

    # Create a Cairo context and scale it
    context = cairo.Context(surface)
    context.scale(size[0]/svg.props.width, size[1]/svg.props.height)

    # Render the SVG
    svg.render_cairo(context)

    # Get image data buffer
    data = surface.get_data()
    if sys.byteorder == 'little':
        # Convert from effective BGRA to actual RGBA.
        # PIL is surprisingly faster than NumPy, but can be done without neither
        data = PIL.Image.frombuffer('RGBA', size, data.tobytes(),
                                    'raw', 'BGRA', 0, 1).tobytes()

    return pygame.image.frombuffer(data, size, "RGBA").convert_alpha()


pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
image = load_svg(PATH, (WIDTH, HEIGHT))
window.blit(image, (0, 0))
pygame.display.update()

clock = pygame.time.Clock()
while True:
    if pygame.event.get([pygame.QUIT]):
        break
    clock.tick(30)
pygame.quit()
