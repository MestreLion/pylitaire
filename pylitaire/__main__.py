# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Convenience package launcher. Allow `python -m pylitaire` invocation."""

from . import main

try:
    main.main()
except KeyboardInterrupt:
    pass
