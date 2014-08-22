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

    clock = pygame.time.Clock()
    dragged_card = None
    drag_button = 0
    clear = False
    done = False
    while not done:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                done = True

            if event.type == pygame.KEYDOWN:

                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    print "New game"
                    game.new_game()
                if event.key == pygame.K_SPACE:
                    print "Restart game"
                    game.restart()

            if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                topcard = game.deck.get_top_card(event.pos)

            if event.type == pygame.MOUSEMOTION:
                if not dragged_card:
                    if topcard and topcard.draggable:
                        pygame.mouse.set_cursor(*g.cursors['draggable'])
                    else:
                        pygame.mouse.set_cursor(*g.cursors['default'])

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not dragged_card:
                    if topcard and topcard.draggable:
                        if not event.button == 3:
                            dragged_card = topcard
                            dragged_card.drag_start(event.pos)
                            drag_button = event.button

            if event.type == pygame.MOUSEBUTTONUP:
                if not dragged_card and topcard and topcard.flippable and event.button == 3:
                    topcard.flip()
                    pygame.mouse.set_cursor(*(g.cursors['draggable'] if topcard.draggable else g.cursors['default']))
                if dragged_card and event.button == drag_button:
                    if drag_button == 1:
                        dragged_card.drag_stop()
                    else:
                        dragged_card.drag_abort()
                    dragged_card = None
                    drag_button = 0

        if dragged_card:
            dragged_card.drag(pygame.mouse.get_pos())

        deck.update()
        graphics.render([deck], clear)
        clear = False

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
