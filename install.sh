#!/usr/bin/env bash
# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

# Debian/Ubuntu installer for Pylitaire and its desktop integration

# System packages needed for apt-installing dependencies:
# PyGObject (gi and cairo): python3-gi python3-gi-cairo gir1.2-gtk-3.0
# Pillow (PIL): python3-pil
# XDG: python3-xdg

# System packages needed for pip-installing dependencies:
# PyGObject from pip: libgirepository1.0-dev gcc libcairo2-dev python3-dev pkg-config
# https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-getting-started
# Pycairo from pip (all included in PyGObject):  libcairo2-dev python3-dev pkg-config
# https://pycairo.readthedocs.io/en/latest/getting_started.html

# System packages needed regardless if pip- or apt-install:
# Rsvg (bindings for librsvg): gir1.2-rsvg-2.0


set -Eeuo pipefail  # exit on any error
trap '>&2 echo "error: line $LINENO, status $?: $BASH_COMMAND"' ERR

slug=pylitaire

self="${0##*/}"
here=$(dirname "$(readlink -f "$0")")

# user settings
system=0
exec=$here/$slug.sh
desktop=$slug.desktop
bindir=${XDG_BIN_HOME:-$HOME/.local/bin}
bin=$bindir/$slug
sudo='env'
packages=(
	python3-pip
	python3-gi-cairo python3-gi-cairo gir1.2-gtk-3.0  # PyGObject (gi.repository)
	gir1.2-rsvg-2.0  # Rsvg (bindings for librsvg)
)
# Latest setuptools available for Python 3.6 (59.x) can't read config in pyproject.toml,
# so we duplicate dependencies here and manually pip-install them without actually
# installing our package
pypackages=(
	Pillow
	pygame
	pyxdg
)

exists(){ type "$@" &>/dev/null; }
install_packages() {
	# Avoid marking installed packages as manual by only installing missing ones
	local pkg=
	local pkgs=()
	local ok
	for pkg in "$@"; do
		# shellcheck disable=SC1083
		ok=$(dpkg-query --showformat=\${Version} --show "$pkg" 2>/dev/null || true)
		if [[ -z "$ok" ]]; then pkgs+=( "$pkg" ); fi
	done
	if (("${#pkgs[@]}")); then
		echo sudo apt install "${pkgs[@]}"
	fi
}
usage() {
	echo "Install Pylitaire and its desktop integration (launcher and icons)"
	echo "See README.md for details"
	echo "Usage: $self [--system]"
	exit "${1:-0}"
}
if (($# > 2)); then usage 1; fi
for arg in "$@"; do if [[ "$arg" == '-h' || "$arg" == '--help' ]]; then usage; fi; done
for arg in "$@"; do if [[ "$arg" == '--system' ]]; then	system=1; else usage 1; fi; done

if ((system)); then
	sudo='sudo'
fi

if ! exists "$slug"; then
	install_packages "${packages[@]}"
	python3 -m pip install "${pypackages[@]}"
	mkdir --parents -- "$bindir"
	rm -f -- "$bin" && ln -s -- "$exec" "$bin"
fi

for icon in "$here"/"$slug"/data/icons/icon-*.png ; do
	size=${icon##*-}; size=${size%%.*}
	"$sudo" xdg-icon-resource install --noupdate --novendor --size "$size" "$icon" "$slug"
done
"$sudo" xdg-icon-resource forceupdate

"$sudo" xdg-desktop-menu install --novendor "$desktop"
