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

    # Init themes
    themes.init_themes()

    # Calculate card size
    # Card height is fixed: 4 cards + margins (top, bottom, 3 between)
    # Card width is free to adjust itself proportionally, according to theme aspect ratio
    # Actual card size is only defined when cards.Deck() renders the theme SVG
    cardsize = (g.window_size[0], (g.window_size[1] - 5 * g.MARGIN[1]) / 4)

    # Create the cards
    deck = cards.Deck(g.theme, cardsize)
    deck.shuffle()

    # Init slots
    graphics.init_slots(deck.cardsize)

    # Game objects
    spritegroups = []
    spritegroups.append(deck)

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

                def restart():
                    for card in deck.cards:
                        card.move(g.MARGIN)
                        deck.move_to_back(card)

                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    print "New game"
                    deck.shuffle()
                    restart()
                if event.key == pygame.K_SPACE:
                    print "Restart game"
                    restart()

            if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                topcard = deck.get_top_card(event.pos)

            if event.type == pygame.MOUSEMOTION:
                if not dragged_card:
                    if topcard and topcard.drag_allowed:
                        pygame.mouse.set_cursor(*g.cursors['draggable'])
                    else:
                        pygame.mouse.set_cursor(*g.cursors['default'])

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not dragged_card:
                    if topcard:
                        dragged_card = topcard
                        dragged_card.drag_start(event.pos)
                        drag_button = event.button
            if event.type == pygame.MOUSEBUTTONUP:
                if dragged_card and event.button == drag_button:
                    if drag_button == 1:
                        dragged_card.drag_stop()
                    else:
                        dragged_card.drag_abort()
                    dragged_card = None
                    drag_button = 0

        if dragged_card:
            dragged_card.drag(pygame.mouse.get_pos())

        # Update
        for group in spritegroups:
            group.update()

        # Draw
        graphics.render(spritegroups, clear)
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
