# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Graphics-related functions."""


import os
import sys
import logging
import math
import array

# Disable Pygame advertisement. Must be done before importing pygame
# https://github.com/pygame/pygame/commit/18a31449de93866b369893057f1e60330b53da95
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = ""  # the key just need to exist
import pygame
import cairo
import PIL.Image
import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

from . import g
from . import cursors

log = logging.getLogger(__name__)

# File extensions of pygame supported image formats
# As documented at http://www.pygame.org/docs/ref/image.html
IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'pcx', 'tga', 'tif', 'tiff',
              'lbm', 'pbm', 'pgm', 'ppm', 'xpm']

_desktop_size = ()


class Background(object):
    def __init__(self, path="", size=(), color=None, title=""):
        """Create a new background of <size> from a <path> image file.

        Use <color> as a fallback for solid fill. If <path> is empty, try to find one
        using an image named <title> in datadirs.

        <color> defaults to g.BGCOLOR.
        <title> defaults to g.baize.
        """
        self.path = path or find_image(g.datadirs('images'), title or g.baize)
        self.color = color or g.BGCOLOR
        self.original = None
        self.surface = None

        if size:
            self.resize(size)

    def resize(self, size):
        """Return surface of <size> rendered with original background image.

        If original image is smaller than (800, 600) then tile it (repeat),
        otherwise re-scale to fit (stretch/shrink).
        """
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
            for i in range(int(math.ceil(float(size[0]) / bgw))):
                for j in range(int(math.ceil(float(size[1]) / bgh))):
                    self.surface.blit(self.original, (i * bgw, j * bgh))

        # Status bar area
        rect = pygame.Rect(0, size[1] - g.SBHEIGHT, size[0], g.SBHEIGHT)
        self.surface.fill(g.SBCOLOR, rect)

    def draw(self, destsurface, position=()):
        """Draw the background to a destination <surface> at <position>.

        <position> defaults to (0, 0).
        """
        destsurface.blit(self.surface, position or (0, 0))


class Slot(object):
    """Slot image."""

    def __init__(self, path="", size=()):
        self.path = path or find_image(g.datadirs('images'), g.slotname, ['svg', 'svgz'])
        self.original = load_vector(self.path)
        self.surface = None

        if size:
            self.resize(size)

    def resize(self, size=()):
        self.surface = render_vector(self.original, size, proportional=False)


def init_graphics(window_size=None, full_screen=None):
    """Initialize the game window and graphics."""

    global _desktop_size

    log.info("Initializing graphics")
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

    # Caption, icon and mouse cursor should be set before window is created
    pygame.display.set_caption("Pylitaire")
    pygame.display.set_icon(pygame.image.load(os.path.join(g.DATADIR, 'icons', 'icon-32.png')))

    for cursor in g.cursors.keys():
        g.cursors[cursor] = cursors.load_json(os.path.join(g.DATADIR,
                                                           'cursors', "%s.json" % cursor))
    pygame.mouse.set_cursor(*g.cursors['default'])

    g.background = Background()
    g.slot = Slot()

    if not _desktop_size:
        # Save the current desktop size once and only once, as pygame only
        # provide this information before the first call to display.set_mode()
        _desktop_size = (pygame.display.Info().current_w,
                         pygame.display.Info().current_h)

    return resize(window_size, full_screen)


def resize(window_size=None, full_screen=None):
    """Resize the window to <window_size> and optionally set <full_screen> mode.

    Both default to current values, so may be set independently. In full screen
    mode, window size is ignored and desktop resolution is used instead.

    Requested values are saved for future runs.
    """
    if window_size is None and full_screen is None:
        return pygame.display.get_surface()

    if window_size is not None: g.window_size = window_size
    if full_screen is not None: g.full_screen = full_screen

    full_screen = g.full_screen
    window_size = g.window_size

    flags = 0
    if full_screen:
        log.debug("Setting full-screen, desktop resolution %r", _desktop_size)
        flags |= pygame.FULLSCREEN
        window_size = _desktop_size
    else:
        log.debug("Setting window size %s", window_size)
        flags |= pygame.RESIZABLE

    # FIXME: avoid calling set_mode() on resize.
    # See https://www.pygame.org/wiki/WindowResizing
    # FIXME: Use pygame.display.toggle_fullscreen() instead of flags on resize
    # http://www.pygame.org/docs/ref/display.html#pygame.display.toggle_fullscreen
    window = pygame.display.set_mode(window_size, flags)
    size = window.get_size()  # actual window size, regardless of mode

    g.background.resize(size)
    g.background.draw(window)

    # Display the window soon as possible, as other elements may take a while
    pygame.display.update()

    # return the new window
    return window


def scale_size(original, size=(), proportional=True, multiple=(1, 1)):
    """Enlarge or shrink <original> size so it fits a <size>.

    If <proportional>, rescaled size will maintain the original width and
    height proportions, so resulting size may be smaller than requested in
    either dimension.

    <multiple> rounds down <size> to be a multiple of given integers. It
    allows themes to ensure cards have integer size, but may slightly change
    image aspect ratio.

    <original>, <size>, <multiple> and the return value are 2-tuple
    (width, height). Returned width and height are rounded to integers.
    """
    def round_to_multiple(s, m):
        return (int(s[0] / m[0]) * m[0],
                int(s[1] / m[1]) * m[1])

    if not size or size == original:
        return round_to_multiple(original, multiple)

    if not proportional:
        return round_to_multiple(size, multiple)

    rect = pygame.Rect((0, 0), original)
    result = rect.fit(pygame.Rect((0, 0), size))
    return round_to_multiple((result.width, result.height), multiple)


def load_image(path, size=(), proportional=True, multiple=(1, 1)) -> pygame.Surface:
    """Wrapper for pygame.image.load, adding support for SVG images.

    See scale_size() for documentation on arguments.

    For regular images, requesting a <size> different from the original (after
    processing aspect, multiple and roundings) will use pygame.transform.smoothscale().
    """
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


def load_svg(path, *scaleargs, **scalekwargs) -> pygame.Surface:
    """Load an SVG file and return a pygame surface.

    See scale_size() for documentation on scale arguments.
    """
    # noinspection PyArgumentList
    return render_vector(load_vector(path), *scaleargs, **scalekwargs)


def load_vector(path) -> Rsvg.Handle:
    """Load an SVG file from <path> and return a vector object."""
    # noinspection PyArgumentList
    return Rsvg.Handle.new_from_file(path)


def render_vector(svg: Rsvg.Handle, *scaleargs, **scalekwargs) -> pygame.Surface:
    """Render a vector object to a pygame surface and return it.

    Vector objects are such as the one returned from load_vector(),
    currently an Rsvg.Handle.
    """

    def bgra_to_rgba(s):
        """Convert a Cairo surface in BGRA format to a RBGA string.

        Only needed for little-endian architectures.
        """
        # PIL generates a memoryview in Python 3+, so we convert to bytes
        d = s.get_data()
        if sys.version_info >= (3, 0):
            d = d.tobytes()
        img = PIL.Image.frombuffer(
            'RGBA', (s.get_width(), s.get_height()),
            d, 'raw', 'BGRA', 0, 1)
        return img.tobytes('raw', 'RGBA', 0, 1)

    # Calculate size
    svgsize = (svg.props.width, svg.props.height)
    width, height = scale_size(svgsize, *scaleargs, **scalekwargs)

    # If new size is different from original, calculate the scale factor
    scale = (1, 1)
    if not (width, height) == svgsize:
        scale = (float(width)/svgsize[0], float(height)/svgsize[1])

    log.debug("Rendering SVG size (%4g,%4g)->(%4g,%4g): %s",
              svgsize[0], svgsize[1], width, height, svg.props.base_uri)

    # Create a Cairo surface. Architecture endianess determines if cairo surface
    # pixel format will be RGBA or BGRA
    if sys.byteorder == 'little':
        dataarray = None
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    else:
        dataarray = array.array('c', chr(0) * width * height * 4)
        surface = cairo.ImageSurface.create_for_data(
            dataarray, cairo.FORMAT_ARGB32, width, height, width * 4)

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
    """Find the first suitable image file in <dirs> and return its full path.

    "Suitable" means being a supported image file, its extension in <exts>, and,
    if <title>, with file title (basename sans extension) matching it.
    """
    for path in dirs:
        try:
            for basename in os.listdir(path):
                filetitle, ext = os.path.splitext(basename.lower())
                if (
                    (not title or title == filetitle) and
                    (not exts or ext[1:] in exts) and
                    (ext[1:] in IMAGE_EXTS+['svg'])
                ):
                    return os.path.join(path, basename)
        except OSError as e:
            # path not found
            if e.errno == 2:
                continue
            else:
                raise
