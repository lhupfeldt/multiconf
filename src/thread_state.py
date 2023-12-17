# Copyright (c) 2012-2020 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import threading

from .envs import MC_NO_ENV

class ThreadState(threading.local):
    def __init__(self):
        super().__init__()
        self.env = MC_NO_ENV
        self.is_under_default_item = False


thread_local = ThreadState()
