#!/usr/bin/make -f
# This file is part of Pylitaire
# Copyright (C) 2022 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

# Tools to process theme SVG files and download additional ones

REPOSITORY = https://gitlab.gnome.org/GNOME/aisleriot/-/raw/gnome-3-20/cards
UBUNTU = https://git.launchpad.net/ubuntu/+source/branding-ubuntu/plain/branding/aisleriot/cards/bonded.svg?h=ubuntu/raring
THEMES = *.svg

all: themes fix-ids crush scour

clean:
	rm -f -- fix-card-ids.ed svgcrush* *.tmp

themes: anglo_bitmap.svg gnome_bonded.svg ubuntu_bonded.svg

# https://gitlab.gnome.org/GNOME/aisleriot/-/commit/950318551392b42967841b63cb7d01cc15495a40
fix-ids: fix-card-ids.ed
	for theme in $(THEMES); do cat $< | red -l "$$theme" 2>&1 | sed '/^\?$$/d' >&2; done

# https://gitlab.gnome.org/GNOME/aisleriot/-/commit/5b4e7ce5a70c7c1a6c1c6ca7088446c50eec6724
# https://gitlab.gnome.org/GNOME/aisleriot/-/commit/41038e7b15b36b7357cfb85053c184314dc56c56
crush: svgcrush
	for theme in $(THEMES); do ./svgcrush "$$theme" "$$theme".tmp; mv "$$theme".tmp "$$theme"; done

# Adapted from Debian/Ubuntu Aisleriot package
# Run it twice for idempotency
scour:
	if ! type scour >/dev/null 2>&1; then sudo apt install scour; fi
	for theme in $(THEMES); do \
		scour "$$theme" "$$theme".tmp; \
		scour "$$theme".tmp "$$theme"; \
		rm -- "$$theme".tmp; \
	done

# -----------------------------------------------------------------------------

gnome_bonded.svg: bonded.svg
	mv -- $< $@

ubuntu_bonded.svg:
	wget -O $@ -- $(UBUNTU)

anglo_bitmap.svg bonded.svg fix-card-ids.ed svgcrush.c:
	wget -- $(REPOSITORY)/$@

# Build commands for adapted from:
# https://gitlab.gnome.org/GNOME/aisleriot/-/blob/gnome-3-20/cards/Makefile.am
# https://gitlab.gnome.org/GNOME/aisleriot/-/blob/master/cards/meson.build
# https://gitlab.gnome.org/GNOME/aisleriot/-/blob/master/cards/meson_svgz.sh
svgcrush: svgcrush.c install-pkg-config
	$(CC) -o $@ $< $(CFLAGS) $(shell pkg-config --cflags --libs glib-2.0 libxml-2.0) $(LDLIBS)

install-pkg-config:
	if ! type pkg-config >/dev/null 2>&1; then sudo apt install pkgconf; fi

.PHONY: all clean themes fix-ids crush scour install-pkg-config
