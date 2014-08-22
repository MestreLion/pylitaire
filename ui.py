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

log = logging.getLogger(__name__)


class MOUSEBUTTONS(g.Enum):
    '''Pygame mouse buttons'''
    NONE      = None
    LEFT      = 1
    MIDDLE    = 2
    RIGHT     = 3
    WHEELUP   = 4
    WHEELDOWN = 5


class Gui(object):
    def __init__(self):
        self.topcard = None
        self.dragcard = None
        self.dragbutton = MOUSEBUTTONS.NONE
        self.updatecursor = False


    def handle_event(self, event, game):
        if (event.type == pygame.QUIT or
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return False

        if event.type == pygame.KEYDOWN:

            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                log.info("New game")
                game.new_game()
            if event.key == pygame.K_SPACE:
                log.info("Restart game")
                game.restart()

        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
            topcard = game.deck.get_top_card(event.pos)
            # "not self.dragcard" test here is needed only because rapid mouse
            # movement may cause topcard != dragcard when mouse momentarily
            # moves out of dragged card
            if topcard != self.topcard and not self.dragcard:
                self.updatecursor = True
            self.topcard = topcard

        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.dragcard:
                if self.topcard and self.topcard.draggable:
                    if not event.button == MOUSEBUTTONS.RIGHT:
                        self.dragcard = self.topcard
                        self.dragcard.drag_start(event.pos)
                        self.dragbutton = event.button
                        self.updatecursor = True
                        log.debug("Start dragging %s", self.dragcard)

        if event.type == pygame.MOUSEBUTTONUP:
            if (event.button == MOUSEBUTTONS.RIGHT and
                not self.dragcard and
                self.topcard and
                self.topcard.flippable):
                self.topcard.flip()
                self.updatecursor = True
                log.debug("Flip card %s", self.topcard)

            if self.dragcard and event.button == self.dragbutton:
                if self.dragbutton == MOUSEBUTTONS.LEFT:
                    self.dragcard.drag_stop()
                    log.debug("Drop %s", self.dragcard)
                else:
                    self.dragcard.drag_abort()
                    log.debug("Abort drag %s", self.topcard)
                self.dragcard = None
                self.dragbutton = MOUSEBUTTONS.NONE
                self.updatecursor = True

        return True


    def update(self):
        if self.dragcard:
            self.dragcard.drag(pygame.mouse.get_pos())

        if self.updatecursor:
            self.updatecursor = False
            if self.dragcard:
                pygame.mouse.set_cursor(*(g.cursors['drag']))
                log.debug("Update cursor to drag")
            else:
                if self.topcard and self.topcard.draggable:
                    pygame.mouse.set_cursor(*(g.cursors['draggable']))
                    log.debug("Update cursor to draggable")
                else:
                    pygame.mouse.set_cursor(*(g.cursors['default']))
                    log.debug("Update cursor to default")
