# -*- coding: utf-8 -*-
'''
libIGCM

author: olivier.marti@lsce.ipsl.fr

GitHub : https://github.com/oliviermarti/IPSLCM-Utilities

This library if a layer under some usefull
environment variables and commands.
All those definitions depend on host particularities.

This software is governed by the CeCILL  license under French law and
abiding by the rules of distribution of free software.  You can  use,
modify and/ or redistribute the software under the terms of the CeCILL
license as circulated by CEA, CNRS and INRIA at the following URL
"http://www.cecill.info".

Warning, to install, configure, run, use any of Olivier Marti's
software or to read the associated documentation you'll need at least
one (1) brain in a reasonably working order. Lack of this implement
will void any warranties (either express or implied).
O. Marti assumes no responsability for errors, omissions,
data loss, or any other consequences caused directly or indirectly by
the usage of his software by incorrectly or partially configured
personal.
'''

from libIGCM.utils import Container

from libIGCM import utils
from libIGCM.utils import set_options, get_options, reset_options, push_stack, pop_stack, return_stack
from libIGCM import date
from libIGCM import sys
from libIGCM import post

