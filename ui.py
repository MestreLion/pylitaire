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

'''GUI functions and classes.

Design notes:
- Can fully use and modify the global values from g module
- Actions that dependent on a game rule use Game methods
- Purely graphical actions, like drag a card, use Deck/Card methods directly
- Resizing IS game rule dependent, as each game sets its own grid
'''

import logging
import datetime

import pygame

import g
import graphics
import gamerules
import enum

log = logging.getLogger(__name__)


class MOUSEBUTTONS(enum.Enum):
    '''Pygame mouse buttons'''
    NONE      = None
    LEFT      = 1
    MIDDLE    = 2
    RIGHT     = 3
    WHEELUP   = 4
    WHEELDOWN = 5


class COLORS(enum.Enum):
    RED        = (255,   0,   0)
    GREEN      = (  0, 255,   0)
    BLUE       = (  0,   0, 255)
    BLACK      = (  0,   0,   0)
    WHITE      = (255, 255, 255)
    GRAY       = (127, 127, 127)


class Quit(Exception):
    pass


class Gui(object):
    def __init__(self, size=()):
        self.size = size
        self.pos = None
        self.card = None
        self.dragcard = None
        self.clickcard = None
        self.doubleclickcard = None
        self.doubleclicktimer = 0
        self.updatecursor = False
        self.cursorname = ""
        self.statustimer = 0
        self.ticks = 0
        self.gamestarttime = 0
        self.updatestatus = False
        self.win = False
        self.clear = False

        self.games = gamerules.get_games()
        self.statusbar = StatusBar(height=g.SBHEIGHT, bgcolor=g.SBCOLOR)
        self.widgets = pygame.sprite.LayeredUpdates(self.statusbar)
        #should be LayeredDirty, but that makes cards/sb interaction glitchy
        self.spritegroups = [self.widgets]

        self.game = None

        if size:
            self.resize(size)


    def load_game(self, gamename):
        self.card = None
        self.dragcard = None
        self.clickcard = None
        self.doubleclickcard = None
        self.doubleclicktimer = 0

        if self.game:
            self.spritegroups.remove(self.game.deck)
            g.background.resize(self.size)  # clear slots

        self.game = gamerules.load_game(gamename)

        self.spritegroups.insert(0, self.game.deck)
        self.resize_board(self.size)
        self.startgame(True)


    def handle_events(self):
        '''Handle all the events generated by pygame
            Return True if game should keep running
        '''
        self.ticks = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type in [pygame.MOUSEMOTION,
                              pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP]:
                self.pos = event.pos
                self._update_card(updatestatus=False)
            try:
                self._handle_event(event, self.game)
            except Quit:
                return False
        return True


    def _update_card(self, force_cursor_update=False, updatestatus=True):
        '''Get the (possibly new) card under mouse position.
            Also, if card is different, flag to update the mouse cursor
            By default also flag to update the status bar message and score
        '''
        if not self.game:
            return
        card = self.game.get_top_card_or_slot(self.pos)
        # mouse cursor is never changed during drag, no matter what
        # current card may be None when mouse is fast and momentarily
        # moves out of dragged card
        if not self.dragcard and (force_cursor_update or card != self.card):
            self.updatecursor = True
        if updatestatus:
            self.updatestatus = True
        self.card = card


    def _handle_event(self, event, game):
        if (event.type == pygame.QUIT or
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            raise Quit

        if event.type == pygame.VIDEORESIZE:
            graphics.resize(event.size)
            self.resize(event.size)

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                self.startgame(new=True)
            if event.key == pygame.K_SPACE:
                self.startgame(new=False)
            if event.key == pygame.K_F1:
                log.debug("HELP!\nHelp me if you can, I'm feeling down,\n"
                          "And I do appreciate you being 'round\n"
                          "Help me get my feet back on the ground\n"
                          "Won't you please, please help me")
            if event.key in xrange(pygame.K_F2, pygame.K_F12+1):
                # A little hack for "get the n-th game"
                i = event.key - pygame.K_F2
                games = sorted(self.games.items())
                if len(games) >= i + 1:
                    self.load_game(games[i][0])

        if self.win or not game:
            return

        if (event.type == pygame.MOUSEBUTTONDOWN
            and self.card):

            if event.button == MOUSEBUTTONS.LEFT:

                self.gamestarttime = self.gamestarttime or self.ticks

                if (self.card == self.doubleclickcard
                    and self.ticks < self.doubleclicktimer):
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
                    self.doubleclicktimer = self.ticks + g.doubleclicklimit

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
        if self.win or not self.game:
            return

        if self.dragcard:
            self.dragcard.drag(pygame.mouse.get_pos())
            for widget in pygame.sprite.spritecollide(self.dragcard,
                                                      self.widgets,
                                                      False):
                widget.dirty = 1

        if self.gamestarttime and self.ticks > self.statustimer:
            self.updatestatus = True
            self.statustimer = self.ticks + 1000

        if self.updatestatus:
            self.updatestatus = False
            self.statusbar.message = self.game.status()
            self.statusbar.time = self.gamestarttime and (self.ticks -
                                                          self.gamestarttime)
            self.statusbar.score = self.game.score()
            self.statusbar.need_update = True
            log.info("%s\t%s\t%s",
                     self.statusbar.message,
                     self.statusbar.time,
                     self.statusbar.score)

            self.win = self.game.win()

        self.game.deck.update()
        for sprite in self.widgets:
            if sprite.need_update:
                sprite.update()

        if self.updatecursor:
            self.updatecursor = False
            # 'drag' is handled directly
            if self.card and self.game.draggable(self.card):
                self.set_mouse_cursor('draggable')
            else:
                self.set_mouse_cursor('default')

        if self.win:
            self.wingame()


    def set_mouse_cursor(self, cursorname):
        if cursorname != self.cursorname:
            pygame.mouse.set_cursor(*(g.cursors[cursorname]))
            log.debug("Update cursor to %s", cursorname)
            self.cursorname = cursorname


    def resize(self, size):
        '''Resize all widgets according to new window <size>
            Also trigger the board resize
        '''
        self.size = size
        for widget in self.widgets:
            widget.resize(size)
        self.resize_board(size)


    def resize_board(self, size):
        '''Recalculate board geometry, resizing and repositioning all board
            elements according to window <size>. Current board elements are:
            - game.deck and its cards, by Deck.resize(maxcardsize)
            - slot image, by its own .resize(cardsize)
            - game.slots, by its own .resize(cardsize)
            - Reposition of game.slots and its cards via .board_move()
            - As a handy hack, draw slots as background
        '''
        if not self.game:
            return

        playarea = pygame.Rect(g.MARGIN,
                               (size[0] - g.MARGIN[0],
                                size[1] - g.MARGIN[1] - self.statusbar.height))
        cellsize = (playarea.width  / self.game.grid[0],
                    playarea.height / self.game.grid[1])
        maxcardsize = (cellsize[0] - g.MARGIN[0],
                       cellsize[1] - g.MARGIN[1])

        self.game.deck.set_theme(g.theme)
        cardsize = self.game.deck.resize(maxcardsize)

        log.debug("Resizing board to %r and card size to %r",
                  playarea, cardsize)

        g.slot.resize(cardsize)
        geometry = pygame.Rect(playarea.topleft, cellsize)
        for slot in self.game.slots:
            slot.resize(cardsize)
            slot.boardmove(geometry)
            slot.draw(g.background.surface, g.slot.surface)

        self.clear = True


    def startgame(self, new=True):
        if not self.game:
            return
        self.set_mouse_cursor('default')
        self.gamestarttime = 0
        self.win = False
        self.updatestatus = True
        if new:
            self.game.new_game()
        else:
            self.game.restart()


    def wingame(self):
        log.info("YOU WIN! In %s, congratulations! Bouncing cards soon, I promise!",
                 formattime(self.ticks - self.gamestarttime))
        self.gamestarttime = 0
        self.win = True


class StatusBar(pygame.sprite.DirtySprite):
    def __init__(self, **params):
        self.height     = params.pop('height', 25)
        self.color      = params.pop('color', COLORS.BLACK)
        self.bgcolor    = params.pop('bgcolor', COLORS.GRAY)
        self.padding    = params.pop('padding', (10, 2))
        font            = params.pop('font', None)
        font_name       = params.pop('font_name',  None)
        font_size       = params.pop('font_size',  24)
        width, height   = params.pop('windowsize', (0, 0))
        super(StatusBar, self).__init__(**params)

        self.font = font or pygame.font.Font(font_name, font_size)

        # dummy until resize()
        self.rect = pygame.Rect(0, 0, 0, 0)
        if width and height:
            self.resize((width, height))

        # All dummy until update()
        self.image  = pygame.Surface((0, 0))
        self.llabel = pygame.Surface((0, 0))
        self.rlabel = pygame.Surface((0, 0))

        self.message = ""
        self.time = 0
        self.score = 0

        self.need_update = True
        self.dirty = 1

    def update(self):
        '''Rebuild all data needed by draw()'''
        self.need_update = False

        self.image = pygame.Surface(self.rect.size)
        self.image.fill(self.bgcolor)

        ltext = self.message
        rtext = "Time: %s    Score: %3d" % (
            formattime(self.time),
            self.score)

        def renderfont(text):
            return self.font.render(text, True, self.color, self.bgcolor)

        llabel = renderfont(ltext)
        rlabel = renderfont(rtext)

        rrect = rlabel.get_rect()
        rrect.bottomright = (self.rect.width  - self.padding[0],
                             self.rect.height - self.padding[1])

        lrect = llabel.get_rect()
        lrect.bottomleft = (self.padding[0],
                            self.rect.height - self.padding[1])

        self.image.blit(llabel, lrect)
        self.image.blit(rlabel, rrect)

        self.dirty = 1

    def resize(self, windowsize):
        '''Recalculate self.rect, return self.height'''
        width, height = windowsize
        self.rect.topleft = (0, height - self.height)
        self.rect.size = (width, self.height)

        self.update()
        return self.height


def formattime(miliseconds):
    return datetime.timedelta(seconds=miliseconds/1000)
