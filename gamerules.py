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

        # all pygame.Rect, and set in resize()
        self.stock = None
        self.waste = None
        self.tableau = []
        self.foundations = []

        self.resize(playarea)
        self.deck.create_cards(faceup=False)

    def resize(self, playarea):
        self.playarea = playarea

        self._grid = (self.playarea.width  / 8,
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
        position = (self.playarea.left + i * self._grid[0],
                    self.playarea.top  + j * self._grid[1])
        g.background.surface.blit(g.slot.surface, position)
        return pygame.Rect(position, g.slot.surface.get_size())

    def new_game(self):
        self.deck.shuffle()
        self.restart()

    def restart(self):
        for card in self.deck.cards:
            card.move(self.playarea.topleft)
            card.flip(faceup=False)
            self.deck.move_to_back(card)

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
