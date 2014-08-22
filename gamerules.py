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

import pygame

import g

log = logging.getLogger(__name__)


class Yukon(object):
    def __init__(self, playarea, deck):
        self.playarea = playarea
        self.deck = deck

        # set in resize(), all but grid are pygame.Rect
        self.stock = None
        self.waste = None
        self.tableau = []
        self.foundations = []
        self.cell = ()  # (width, height) of game "cell" (cardsize + margins)

        self.resize(playarea)

        self.deck.create_cards(faceup=False)

    def resize(self, playarea):
        self.playarea = playarea

        self.cell = (self.playarea.width  / 8,
                     self.playarea.height / 4)

        self.stock = self._game_slot(0, 0)
        self.waste = self._game_slot(1, 0)

        self.foundations = []
        for i in (4, 5, 6, 7):
            self.foundations.append(self._game_slot(i, 0))

        self.tableau = []
        for i in xrange(8):
            self.tableau.append(self._game_slot(i, 1))

    def _game_slot(self, i, j):
        # this function probably go to an API module, class method or base class
        # it is the only code that requires g and pygame to be imported, thus
        # preventing true decoupling
        position = (self.playarea.left + i * self.cell[0],
                    self.playarea.top  + j * self.cell[1])
        g.background.surface.blit(g.slot.surface, position)
        return pygame.Rect(position, g.slot.surface.get_size())

    def new_game(self):
        self.deck.shuffle()
        self.restart()

    def restart(self):
        c = 0
        e = 2  # extra cards in each column
        for row in xrange(8 + e):
            # 0.18 would be 0.2 if not for margin (cardsize instead of cell)
            top = self.tableau[0].top + 0.18 * row * self.cell[1]
            for col in xrange(max(0, row - e), 8):
                left = self.tableau[col].left
                card = self.deck.cards[c]
                card.flip(row >= col)
                card.move((left, top))
                self.deck.move_to_front(card)
                c += 1
        # Stock - should be empty
        for card in self.deck.cards[c:]:
            card.flip(faceup=False)
            card.move(self.stock.topleft)
            self.deck.move_to_front(card)

    def click(self, card):
        '''Click on a card. Return True if card state changed'''
        card.flip()  # for now, outside the IF
        if card.rect.topleft == self.stock.topleft:
            card.move(self.waste.topleft)
        return True

    def flippable(self, card):
        return True

    def draggable(self, card):
        return card.faceup
