##############################################################################
#
# Copyright 2008 Lovely Systems GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
##############################################################################

import unittest, doctest
from zope.testing.doctestunit import DocFileSuite, DocTestSuite

def test_suite():
    dispatcher = DocFileSuite('dispatcher.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
                             )
    proxy = DocFileSuite('proxy.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
                             )
    wsgi = DocFileSuite('wsgi.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
                             )
    tornado = DocFileSuite('tornadohandler.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
                             )
    s = unittest.TestSuite((dispatcher, proxy, wsgi, tornado))
    return s
