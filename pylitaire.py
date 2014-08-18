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

    if g.debug:
        logging.root.level = logging.DEBUG

    pygame.init()
    graphics.init_graphics()

    # Card height = (screen height - 10% margin) / 4, hence 9/40
    themes.init_themes((g.window_size[0], g.window_size[1] * 9 / 40.))

    # Create the cards
    deck = cards.Deck()
    deck.shuffle()

    # Game objects
    sprites = pygame.sprite.OrderedUpdates()
    sprites.add(deck.cards[:10])

    def find_card(cardlist, x, y):
        reversedlist = reversed([card for card in cardlist])
        for card in reversedlist:
            if card.rect.collidepoint(x, y):
                return card

    clock = pygame.time.Clock()

    dragged_card = None
    clear = False
    done = False
    while not done:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    # New game
                    print "New game"
                    for card in sprites:
                        card.rect.topleft = (0, 0)
                if event.key == pygame.K_SPACE:
                    # draw card
                    print "Draw card"

            if event.type == pygame.MOUSEBUTTONDOWN:
                dragged_card = find_card(sprites, *pygame.mouse.get_pos())
            if event.type == pygame.MOUSEBUTTONUP:
                dragged_card = None

        if dragged_card:
            dragged_card.rect.center = pygame.mouse.get_pos()

        # Update
        sprites.update()

        # Draw
        graphics.render(sprites, clear)
        clear = False

        clock.tick(g.FPS)

    pygame.quit()
    return True




if __name__ == "__main__":
    logging.basicConfig()
    log = logging.getLogger(g.GAMENAME)
    sys.exit(0 if main(*sys.argv[1:]) else 1)
