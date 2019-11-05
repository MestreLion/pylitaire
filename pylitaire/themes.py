# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Card Theme handling"""

# TODO:
# - Enable theme resize, adding resize() to Theme. To avoid file reload
#   save cairo context/surface in Theme and split load_svg() in 2 functions

import os
import sys
import logging

import pygame

from . import graphics

log = logging.getLogger(__name__)

# Dict {id: <object>} of all themes found by init_themes()
themes = {}

class Theme(object):
    ''' Represents each card theme '''

    def __init__(self, themeid, path, name=""):
        self.id = themeid
        self.path = path
        self.name = name or self.id.replace("_", " ").title()
        self._image = None
        self.size = ()

    @property
    def image(self):
        ''' Lazy image load '''
        if not self._image:
            self._image = graphics.load_vector(self.path)
            self.size = (self.image.props.height,
                         self.image.props.width)
        return self._image

    @property
    def card_proportion(self):
        ''' Defined as card height / width '''
        return (self.image.props.height / 5.) / (self.image.props.width / 13.)

    def render(self, cardsize=(), proportional=True):
        ''' Render the theme image into a pygame surface and return it '''
        size = cardsize and (cardsize[0] * 13,
                             cardsize[1] *  5)
        return graphics.render_vector(self.image, size, proportional, multiple=(13, 5))



def init_themes(paths):
    ''' Load all themes found in THEMEDIRS and populate the global themes dict
        cardsize and keep_aspect have the same meaning as in load_svg()
    '''

    for path in paths:
        log.debug("Looking for card themes in: %s", path)
        try:
            for basename in os.listdir(path):

                # Check if it's an SVG or SVGZ
                if os.path.splitext(basename)[1].lower() not in ('.svg', '.svgz'):
                    continue

                # Check if it's already added (same basename)
                themeid = os.path.splitext(basename)[0]
                if themeid in themes:
                    continue

                # Create the theme and add it to the dict
                log.debug("New card theme found: %s", themeid)
                themes[themeid] = Theme(themeid, os.path.join(path, basename), name="")

        except OSError as e:
            # path not found
            if e.errno == 2:
                continue
            else:
                raise




if __name__ == '__main__':

    def pause():
        pygame.display.update()
        done = False
        halt = AUTO
        pygame.event.clear()
        while not (done or halt):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or getattr(event, 'key', None) == pygame.K_ESCAPE:
                    halt = True
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    done = True
            clock.tick(10)
        screen.fill(BGCOLOR)
        return halt

    # unit tests

    # constants
    BGCOLOR = (0, 80, 16)
    AUTO = '--auto' in sys.argv[1:]
    THEME = 'bonded'  # the only one that ships with Aisleriot without gnome-cards
    PATH = '/usr/share/aisleriot/cards/%s.svgz' % THEME
    SIZE = (800, 600)

    # setup
    logging.basicConfig(level=logging.DEBUG)
    pygame.display.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(SIZE)
    screen.fill(BGCOLOR)

    # load_svg()
    screen.blit(graphics.load_svg(PATH, SIZE), (0,0))
    pause()

    # Theme()
    theme = Theme(THEME, PATH)
    print(theme.id, theme.name, theme.path, theme.size, theme.card_proportion)
    screen.blit(graphics.render_vector(theme.image), (0,0))
    pause()

    # init_themes()
    init_themes()
    for themeid, theme in sorted(themes.items()):
        print(themeid, theme.card_proportion)
        screen.blit(graphics.render_vector(theme.image, size=SIZE), (0,0))
        if pause():
            break
