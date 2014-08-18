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
# Card Theme handling

# TODO:
# - Enable theme resize, adding resize() to Theme. To avoid file reload
#   save cairo context/surface in Theme and split load_svg() in 2 functions

import os
import sys
import logging

import pygame

import g
import graphics

log = logging.getLogger(__name__)

THEMEDIRS = [
    os.path.join(g.CONFIGDIR, 'themes'),
    os.path.join(g.DATADIR, 'themes'),
    '/usr/share/aisleriot/cards',
]

# Dict {id: <object>} of all themes found by init_themes()
themes = {}

class Theme(object):
    ''' Represents each card theme '''

    def __init__(self, id, path, name="", cardsize=(), keep_aspect=True):
        self.id = id
        self.path = path
        self.name = name or self.id.replace("_", " ").title()

        size = cardsize and (cardsize[0] * 13,
                             cardsize[1] *  5)
        self.surface = graphics.load_image(self.path, size, keep_aspect)

        self.size = self.surface.get_size()
        self.cardsize = (self.size[0] / 13,
                         self.size[1] /  5)
        self.aspect = self.cardsize[1] / self.cardsize[0]


def init_themes(cardsize=(), keep_aspect=True):
    ''' Load all themes found in THEMEDIRS and populate the global themes dict
        cardsize and keep_aspect have the same meaning as in load_svg()
    '''

    for path in THEMEDIRS:
        log.debug("Looking for card themes in: %s", path)
        try:
            for basename in os.listdir(path):

                # Check if it's an SVG
                if not os.path.splitext(basename)[1].lower() == '.svg':
                    continue

                # Check if it's already added (same basename)
                id = os.path.splitext(basename)[0]
                if id in themes:
                    continue

                # For now, load only the default theme
                # No in-game switching yet, and pre-loading all is *very* expensive
                if not id == g.theme:
                    continue

                # Create the theme and add it to the dict
                log.debug("New card theme found: %s", id)
                themes[id] = Theme(id, os.path.join(path, basename), name="",
                                   cardsize=cardsize, keep_aspect=keep_aspect)

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
        exit = AUTO
        pygame.event.clear()
        while not (done or exit):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or getattr(event, 'key', None) == pygame.K_ESCAPE:
                    exit = True
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    done = True
            clock.tick(10)
        screen.fill(g.BGCOLOR)
        return exit

    # unit tests

    # constants
    AUTO = '--auto' in sys.argv[1:]
    TESTTHEME = os.path.join(g.DATADIR, 'themes', 'anglo.svg')

    # setup
    logging.basicConfig(level=logging.DEBUG)
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(g.window_size)
    screen.fill(g.BGCOLOR)

    # load_svg()
    screen.blit(graphics.load_svg(TESTTHEME, g.window_size), (0,0))
    pause()

    # Theme()
    theme = Theme(g.GAMENAME, TESTTHEME)
    print theme.id, theme.name, theme.path, theme.size, theme.cardsize, theme.aspect
    screen.blit(theme.surface, (0,0))
    pause()

    # init_themes()
    init_themes()
    for id, theme in sorted(themes.items()):
        print id, theme.cardsize
