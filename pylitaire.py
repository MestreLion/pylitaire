#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# pylitaire - Solitaire in Python
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
#
# Main module and entry point for Pylitaire

import sys
import logging

import pygame

import g
import graphics
import cards
import themes
import gamerules
import ui

log = logging.getLogger(__name__)


def main(*argv):
    """ Main Program """

    # Too lazy for argparse right now
    if "--fullscreen" in argv: g.fullscreen = True
    if "--debug"      in argv: g.debug = True
    if "--profile"    in argv: g.profile = True

    if g.debug:
        logging.root.level = logging.DEBUG

    pygame.display.init()
    graphics.init_graphics()
    themes.init_themes()

    deck = cards.Deck(g.theme, g.cardsize)
    game = gamerules.Yukon(g.playarea, deck)
    game.new_game()

    gui = ui.Gui(game)

    clock = pygame.time.Clock()
    run = True
    while run:
        run = gui.handle_events()

        gui.update()
        deck.update()
        graphics.render([deck])

        if g.profile:
            return True

        clock.tick(g.FPS)

    pygame.quit()
    return True




if __name__ == "__main__":
    logging.basicConfig()
    log = logging.getLogger(g.GAMENAME)
    try:
        sys.exit(0 if main(*sys.argv[1:]) else 1)
    except KeyboardInterrupt:
        pass
