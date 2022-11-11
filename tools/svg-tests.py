#!/usr/bin/env python3
# This file is part of Pylitaire
# Copyright (C) 2022 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""
SVG renderers testing
"""
import logging
import os.path
import sys
import time

import pygame

log = logging.getLogger(__name__)

DATADIR = os.path.join(os.path.dirname(__file__), '../pylitaire/data/themes')
AISLERIOT = "/usr/share/aisleriot/cards"
IMAGES = []
for _d in (DATADIR, AISLERIOT):
    IMAGES.extend(sorted(os.path.join(_d, _) for _ in os.listdir(_d)
                         if _[-4:] in ('.svg', 'svgz')))
FPS = 60
BGCOLOR = (0, 80, 16)
PROFILE = '--profile' in sys.argv
START_TIME = start_time = time.time()


def load_svg_pygame(path: str, size):
    surface = pygame.image.load(path)
    # To preserve aspect see https://stackoverflow.com/a/73384976/624066
    surface = pygame.transform.smoothscale(surface, size)
    return surface


def load_svg_cairosvg(path: str, size):
    import io
    import cairosvg
    buffer = cairosvg.svg2png(url=path,  # background_color='transparent',
                              output_width=size[0], output_height=size[1])
    surface = pygame.image.load(io.BytesIO(buffer))
    return surface


def load_svg_librsvg(path: str, size):
    import cairo
    import PIL.Image
    import gi
    import numpy
    gi.require_version('Rsvg', '2.0')
    from gi.repository import Rsvg

    def load_vector(p):
        return Rsvg.Handle.new_from_file(p)

    def prepare(vec, sz):
        # Nominally ARGB, but in little-endian architectures it is effectively BGRA
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, *sz)
        c = cairo.Context(s)
        c.scale(sz[0] / vec.props.width, sz[1] / vec.props.height)
        return s, c

    def rsvg_render(vec, c):
        vec.render_cairo(c)

    def convert_bgra_pil(d):
        return PIL.Image.frombuffer('RGBA', size, d.tobytes(),
                                    'raw', 'BGRA', 0, 1).tobytes()

    def convert_bgra_numpy(d):
        d = numpy.frombuffer(d, dtype=numpy.uint8).copy()
        d.shape = (*size, 4)
        # d[..., :3] = d[..., 2::-1]
        d[:, :, [0, 2]] = d[:, :, [2, 0]]
        return d

    # Load the SVG image file
    svg = load_vector(path)
    # Create a Cairo surface and (scaled) context
    surface, context = prepare(svg, size)
    # render the SVG
    rsvg_render(svg, context)
    # Get image data buffer
    data = surface.get_data()
    if sys.byteorder == 'little':
        # Convert from effective BGRA to actual RGBA.
        # PIL is surprisingly faster than NumPy, but can be done without neither
        data = convert_bgra_pil(data)
        # data = convert_bgra_numpy(data)

    return pygame.image.frombuffer(data, size, "RGBA").convert_alpha()


def _load_svg_svglib(path: str, size):
    # Disabled:
    # - Too many visual errors
    # - Insane console output ("x_order_2: colinear!" and such)
    # - Freezes on life_and_smooth.svg
    if 'life_and_smooth.svg' in path:
        raise ValueError("Freezes")
    import io
    import svglib.svglib
    drawing = svglib.svglib.svg2rlg(path)
    buffer = drawing.asString("png")
    surf = pygame.image.load(io.BytesIO(buffer))
    return pygame.transform.smoothscale(surf, size)


def load_image(func_idx: int, path_idx: int):
    func = RENDERERS[func_idx]
    path = IMAGES[path_idx]
    image = os.path.basename(path)
    pygame.display.set_caption(f"{funcname(func)}: {image}")
    dest = pygame.display.get_surface()
    dest.fill(BGCOLOR)
    size = dest.get_size()
    runtime()
    try:
        surf = func(path, size)
    except Exception as e:
        log.error("FAIL: %s [%s]", image, e)
        return
    log.info("%5s: %s", runtime(), image)
    dest.blit(surf, (0, 0))


def runtime(start=0.0):
    global start_time
    now = time.time()
    if start:
        start_time = start
    fmt = "{:.0f}".format(1000 * (now - start_time))
    start_time = now
    return fmt


def funcname(func):
    return func.__name__.split('_', 2)[-1].upper()


def run(f=0, i=0):
    log.info("Renderer: %s", funcname(RENDERERS[f]))
    start = time.time()
    if not PROFILE:
        load_image(f, i)
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if (
                event.type == pygame.QUIT or
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                return
            if event.type == pygame.VIDEORESIZE:
                load_image(f, i)
            elif (
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or
                    (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)  # LEFT
            ):
                i = (i + 1) % len(IMAGES)
                load_image(f, i)
            elif (
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN) or
                    (event.type == pygame.MOUSEBUTTONDOWN and event.button == 3)  # RIGHT
            ):
                f = (f + 1) % len(RENDERERS)
                load_image(f, i)
        pygame.display.update()
        if PROFILE:
            i += 1
            if i == len(IMAGES):
                log.info("%5s: %s total", runtime(start), funcname(RENDERERS[f]))
                return
            load_image(f, i)
        else:
            clock.tick(FPS)


def main():
    logging.basicConfig(
        format="[%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    logging.getLogger('svglib.svglib').setLevel(0)
    pygame.init()
    pygame.display.set_mode(flags=pygame.RESIZABLE)
    log.info("%5s: Loading", runtime())
    if PROFILE:
        for f in range(len(RENDERERS)):
            run(f)
    else:
        run()
    pygame.quit()


RENDERERS = [_v for _k, _v in globals().items() if _k.startswith('load_svg_')]
if __name__ == '__main__':
    sys.exit(main())
