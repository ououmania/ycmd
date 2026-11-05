# Copyright (C) 2026 ycmd contributors
#
# This file is part of ycmd.
#
# ycmd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ycmd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

from hamcrest import assert_that, equal_to
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ycmd import user_options_store
from ycmd.completers.cpp.clangd_completer import ClangdCompleter
from ycmd.server_state import ServerState
from ycmd.tests import IsolatedYcmd
from ycmd.tests.test_utils import DummyCompleter


def _NewCompleter():
  return DummyCompleter( user_options_store.DefaultOptions() )


class DetachTest( TestCase ):
  def test_Completer_DefaultDoesNotKeepAliveOnClientDetach( self ):
    assert_that( _NewCompleter().ShouldKeepAliveOnClientDetach(),
                 equal_to( False ) )


  def test_ClangdCompleter_KeepsAliveOnClientDetach( self ):
    with patch.object( ClangdCompleter, '__init__', return_value = None ):
      completer = ClangdCompleter( user_options_store.DefaultOptions() )
    assert_that( completer.ShouldKeepAliveOnClientDetach(),
                 equal_to( True ) )


  def test_ServerState_Detach_ShutsDownOnlyNonReusableCompleters( self ):
    state = ServerState( user_options_store.DefaultOptions() )
    proto = _NewCompleter()
    clangd = _NewCompleter()
    proto.Shutdown = MagicMock()
    clangd.Shutdown = MagicMock()
    proto.ShouldKeepAliveOnClientDetach = lambda: False
    clangd.ShouldKeepAliveOnClientDetach = lambda: True
    state._filetype_completers = { 'proto': proto,
                                   'cpp': clangd,
                                   'c': clangd }

    state.ShutdownCompletersOnClientDetach()

    proto.Shutdown.assert_called_once_with()
    clangd.Shutdown.assert_not_called()
    assert_that( state._filetype_completers,
                 equal_to( { 'cpp': clangd, 'c': clangd } ) )


  def test_ServerState_Detach_DeduplicatesSharedInstances( self ):
    state = ServerState( user_options_store.DefaultOptions() )
    proto = _NewCompleter()
    proto.Shutdown = MagicMock()
    proto.ShouldKeepAliveOnClientDetach = lambda: False
    state._filetype_completers = { 'proto': proto, 'proto_alt': proto }

    state.ShutdownCompletersOnClientDetach()

    proto.Shutdown.assert_called_once_with()
    assert_that( state._filetype_completers, equal_to( {} ) )


  @IsolatedYcmd()
  def test_DetachHandler_ShutsDownNonReusableCompleters( self, app ):
    completer = _NewCompleter()
    completer.Shutdown = MagicMock()
    with patch.dict( 'ycmd.handlers._server_state._filetype_completers',
                     { 'proto': completer } ):
      assert_that( app.post_json( '/detach', {} ).json, equal_to( True ) )
    completer.Shutdown.assert_called_once_with()
