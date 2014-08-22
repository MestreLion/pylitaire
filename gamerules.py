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
# Game rules and logic

import logging

import g

log = logging.getLogger(__name__)


class Yukon(object):
    def __init__(self, playarea, deck):
        self.playarea = playarea
        self.deck = deck

        self.resize(playarea)
        self.deck.create_cards(faceup=False)

    def resize(self, playarea):
        self.playarea = playarea

        grid = (self.playarea.width  / 8,
                self.playarea.height / 4)

        # Stock, Waste, Foundations
        top = self.playarea.top
        for i in (0, 1, 4, 5, 6, 7):
            g.background.surface.blit(g.slot.surface,
                                      (self.playarea.left + i * grid[0], top))

        # Tableau
        top = self.playarea.top + grid[1]
        for i in xrange(8):
            g.background.surface.blit(g.slot.surface,
                                      (self.playarea.left + i * grid[0], top))

    def new_game(self):
        self.deck.shuffle()
        self.restart()

    def restart(self):
        for card in self.deck.cards:
            card.move(self.playarea.topleft)
            card.flip(faceup=False)
            self.deck.move_to_back(card)

    def click(self, card):
        card.flip()
        return True

    def flippable(self, card):
        return True

    def draggable(self, card):
        return card.faceup
