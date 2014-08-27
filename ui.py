# -*- coding: utf-8 -*-
#
#    Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#    This file is part of Pylitaire gamerules
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
# GUI-related functions and classes

import logging

import pygame

import g
import graphics

log = logging.getLogger(__name__)


class MOUSEBUTTONS(g.Enum):
    '''Pygame mouse buttons'''
    NONE      = None
    LEFT      = 1
    MIDDLE    = 2
    RIGHT     = 3
    WHEELUP   = 4
    WHEELDOWN = 5


class Quit(Exception):
    pass

class Gui(object):
    def __init__(self, game):
        self.game = game
        self.pos = None
        self.card = None
        self.dragcard = None
        self.clickcard = None
        self.doubleclickcard = None
        self.doubleclicktimer = 0
        self.updatecursor = False
        self.cursorname = 'default'

    def handle_events(self):
        '''Handle all the events generated by pygame
            Return True if game should keep running
        '''
        for event in pygame.event.get():
            if event.type in [pygame.MOUSEMOTION,
                              pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP]:
                self.pos = event.pos
                self._update_card()
            try:
                self._handle_event(event, self.game)
            except Quit:
                return False
        return True


    def _update_card(self, force_cursor_update=False):
        '''Get the (possibly new) card under mouse position.
            Also, if card is different, flag to update the mouse cursor
        '''
        card = self.game.get_top_card_or_slot(self.pos)
        # mouse cursor is never changed during drag, no matter what
        # current card may be None when mouse is fast and momentarily
        # moves out of dragged card
        if not self.dragcard and (force_cursor_update or card != self.card):
            self.updatecursor = True
        self.card = card

    def _handle_event(self, event, game):
        if (event.type == pygame.QUIT or
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            raise Quit

        if event.type == pygame.VIDEORESIZE:
            graphics.resize(event.size)
            game.deck.resize(g.cardsize)
            game.resize(g.playarea)

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                game.new_game()
            if event.key == pygame.K_SPACE:
                game.restart()

        elif (event.type == pygame.MOUSEBUTTONDOWN
            and self.card):

            if event.button == MOUSEBUTTONS.LEFT:

                if (self.card == self.doubleclickcard
                    and pygame.time.get_ticks() < self.doubleclicktimer):
                    log.debug("DOUBLE click %s", self.card)
                    self.doubleclickcard = None
                    self.doubleclicktimer = 0
                    if game.doubleclick(self.card):
                        # if game lies, mouse cursor will not be updated
                        self._update_card()
                else:
                    if game.draggable(self.card):
                        log.debug("Start dragging %s", self.card)
                        self.dragcard = self.card
                        self.dragcard.start_drag(self.pos)
                        self.set_mouse_cursor('drag')
                    self.clickcard = self.doubleclickcard = self.card
                    self.doubleclicktimer = pygame.time.get_ticks() + g.doubleclicklimit

            elif event.button == MOUSEBUTTONS.RIGHT:
                # Reserved for start peep
                pass

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == MOUSEBUTTONS.LEFT:

                if self.dragcard:
                    # GUI assumptions for drop candidates, hope any game is OK:
                    # - not itself (duh)
                    # - not one of its descendants (fair enough)
                    # Note that it *does* allow drop on a card that has a child
                    # It's up for the game rules to decide on that
                    candidates = pygame.sprite.Group(*self.game.deck)
                    candidates.remove(self.dragcard, *self.dragcard.children)
                    candidates.add(*self.game.slots)
                    targetcards = pygame.sprite.spritecollide(self.dragcard, candidates, False)

                    # Ask the game which candidates are valid drop targets
                    # Will also be asked on MOUSEMOVE for target highlight
                    dropcards = game.droppable(self.dragcard, targetcards)
                    if dropcards:
                        dropcard = dropcards[0]  # should choose the closest
                        log.debug("Drop %s onto %s", self.dragcard, dropcard)
                        # let the game itself drop, as GUI shall not assume card
                        # will stack, or just snap, or leave position alone
                        # GUI job is just to end the card drop
                        self.dragcard.drop()
                        self.game.drop(self.dragcard, dropcard)
                    else:
                        log.debug("Abort drag %s", self.dragcard)
                        self.dragcard.abort_drag()
                    self.dragcard = None
                    self._update_card(True)

                if self.clickcard:
                    if self.card == self.clickcard:
                        log.debug("Click card %s", self.card)
                        if game.click(self.card):
                            # card may be the same, cursor may be not, hence forced
                            self._update_card(True)
                            # if click changes state, cancel double click
                            # otherwise may turn & move in next mousedown
                            self.doubleclickcard = None
                            self.doubleclicktimer = 0
                    self.clickcard = None

            elif event.button == MOUSEBUTTONS.RIGHT:
                # Reserved for end peep
                pass


    def update(self):
        if self.dragcard:
            self.dragcard.drag(pygame.mouse.get_pos())

        if self.updatecursor:
            self.updatecursor = False
            # 'drag' is handled directly
            if self.card and self.game.draggable(self.card):
                self.set_mouse_cursor('draggable')
            else:
                self.set_mouse_cursor('default')


    def set_mouse_cursor(self, cursorname):
        if cursorname != self.cursorname:
            pygame.mouse.set_cursor(*(g.cursors[cursorname]))
            log.debug("Update cursor to %s", cursorname)
            self.cursorname = cursorname
