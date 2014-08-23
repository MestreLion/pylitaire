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
import cards

log = logging.getLogger(__name__)


class Yukon(object):
    def __init__(self, playarea, deck):
        self.playarea = playarea
        self.deck = deck
        self.slots = []

        # set in resize(), all but grid are pygame.Rect
        self.tableau = []
        self.foundations = []
        self.cell = ()  # (width, height) of game "cell" (cardsize + margins)

        self.resize(playarea)

        self.deck.create_cards(faceup=False)

    def resize(self, playarea):
        self.playarea = playarea

        self.cell = (self.playarea.width  / 8,
                     self.playarea.height / 4)

        self.foundations = []
        for i in (4, 5, 6, 7):
            self.foundations.append(self._game_slot(i, 0))

        self.tableau = []
        for i in xrange(8):
            self.tableau.append(self._game_slot(i, 1))

        # Perhaps should go in _game_slot()
        self.slots = self.tableau + self.foundations

    def _game_slot(self, i, j):
        # this function probably go to an API module, class method or base class
        # it is the only code that requires g and pygame to be imported, thus
        # preventing true decoupling
        position = (self.playarea.left + i * self.cell[0],
                    self.playarea.top  + j * self.cell[1])
        g.background.surface.blit(g.slot.surface, position)
        return pygame.Rect(position, g.slot.surface.get_size())

    def new_game(self):
        self.restart(True)

    def restart(self, new=False):
        if new:
            log.info("New game")
            self.deck.shuffle()
        else:
            log.info("Restart game")
        self.deck.pop_cards()

        c = 0
        e = 2  # extra cards in each column
        for col in xrange(8):
            x = self.tableau[col].x
            for row in xrange(col + 1 + e):
                card = self.deck.cards[c]
                card.flip(row >= col)
                if row == 0:
                    y = self.tableau[0].y
                    card.move((x, y))
                else:
                    card.stack(self.deck.cards[c-1])
                c += 1

    def click(self, card):
        '''Handle click on <card>. Return True if card state changed'''
        if card.stacktail and not card.faceup:
            card.flip(True)
            return True

    def doubleclick(self, card):
        '''Handle double click on <card>. Return True if card state changed'''
        if not card.stacktail or not card.faceup:
            return

        # So this much for DRY... API needs a fake card representing a slot ASAP
        # Also a sprite Group for foundation
        # whole function would be something like:
        # targeds = droppable(card, *FoundationGroup(*[SlotFakeCard(position=f.rect,...)
        #                                              for f in self.foundation]))
        # if targets:
        #     self.drop(targets[0])
        if (card.rank == cards.RANK.ACE or
            self.deck.card(card.rank - 1, card.suit).rect in self.foundations):
            card.pop()
            card.move(self.foundations[card.suit-1].topleft)
            return True

    def drop(self, card, target):
        '''Handle <card> dropped onto <target>'''
        if target.rect in self.foundations:
            orientation = cards.ORIENTATION.PILE
        else:
            orientation = cards.ORIENTATION.DOWN
        card.stack(target, orientation)

    def draggable(self, card):
        '''Return True if card can be dragged.
            Used to set mouse cursor. Actual drag is performed by GUI
        '''
        return card.faceup  # and not card.rect in self.foundations

    def droppable(self, card, targets):
        '''Return a subset of <targets> that are valid drop cards for <card>'''
        droplist = []
        for target in targets:

            if target.rect in self.foundations:
                if (card.stacktail
                    and (card.rank == cards.RANK.ACE
                         or self.deck.card(card.rank - 1, card.suit).rect
                            in self.foundations)):
                    droplist.append(target)

            elif (target.faceup
                  and target.stacktail
                  and target.color != card.color
                  and target.rank == card.rank + 1):
                droplist.append(target)

        return droplist
