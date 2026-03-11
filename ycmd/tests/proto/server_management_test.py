# Copyright (C) 2024 ycmd contributors
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

from hamcrest import assert_that, contains_exactly, equal_to, has_entry
from unittest.mock import patch
from unittest import TestCase

from ycmd.completers.language_server.language_server_completer import (
    LanguageServerConnectionTimeout )
from ycmd.tests.proto import ( IsolatedYcmd,
                               PathToTestFile,
                               StartProtoCompleterServerInDirectory )
from ycmd.tests.test_utils import ( BuildRequest,
                                    MockProcessTerminationTimingOut,
                                    WaitUntilCompleterServerReady )


BUFLS_PATCH = ( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/usr/local/bin/bufls' )
FIND_EXE_PATCH = ( 'ycmd.utils.FindExecutableWithFallback',
                   lambda x, fb: fb )


def AssertProtoCompleterServerIsRunning( app, is_running ):
  request_data = BuildRequest( filetype = 'proto' )
  assert_that( app.post_json( '/debug_info', request_data ).json,
               has_entry(
                 'completer',
                 has_entry( 'servers', contains_exactly(
                   has_entry( 'is_running', is_running )
                 ) )
               ) )


class ServerManagementTest( TestCase ):
  @IsolatedYcmd()
  @patch( *BUFLS_PATCH )
  @patch( *FIND_EXE_PATCH )
  def test_ServerManagement_StartServer_Fails( self, app, *args ):
    """When bufls fails to connect, server is marked as not running."""
    with patch( 'ycmd.completers.language_server.language_server_completer.'
                'LanguageServerConnection.AwaitServerConnection',
                side_effect = LanguageServerConnectionTimeout ):
      filepath = PathToTestFile( 'proto_project', 'test.proto' )
      resp = app.post_json( '/event_notification',
                     BuildRequest(
                       event_name = 'FileReadyToParse',
                       filetype = 'proto',
                       filepath = filepath,
                       contents = ''
                     ) )

      assert_that( resp.status_code, equal_to( 200 ) )

      request_data = BuildRequest( filetype = 'proto' )
      assert_that( app.post_json( '/debug_info', request_data ).json,
                   has_entry(
                     'completer',
                     has_entry( 'servers', contains_exactly(
                       has_entry( 'is_running', False )
                     ) )
                   ) )


  @IsolatedYcmd()
  @patch( *BUFLS_PATCH )
  @patch( *FIND_EXE_PATCH )
  def test_ServerManagement_StopServer( self, app, *args ):
    """StopServer command marks server as not running."""
    filepath = PathToTestFile( 'proto_project', 'test.proto' )

    with patch( 'ycmd.completers.language_server.language_server_completer.'
                'LanguageServerConnection.AwaitServerConnection',
                side_effect = LanguageServerConnectionTimeout ):
      StartProtoCompleterServerInDirectory(
          app, PathToTestFile( 'proto_project' ) )

    app.post_json(
      '/run_completer_command',
      BuildRequest(
        filepath = filepath,
        filetype = 'proto',
        command_arguments = [ 'StopServer' ],
      ),
    )

    AssertProtoCompleterServerIsRunning( app, False )


  @IsolatedYcmd()
  @patch( *BUFLS_PATCH )
  @patch( *FIND_EXE_PATCH )
  @patch( 'shutil.rmtree', side_effect = OSError )
  @patch( 'ycmd.utils.WaitUntilProcessIsTerminated',
          MockProcessTerminationTimingOut )
  def test_ServerManagement_CloseServer_Unclean( self, app, *args ):
    """Unclean server shutdown (e.g. process won't die) is handled gracefully."""
    with patch( 'ycmd.completers.language_server.language_server_completer.'
                'LanguageServerConnection.AwaitServerConnection',
                side_effect = LanguageServerConnectionTimeout ):
      StartProtoCompleterServerInDirectory(
          app, PathToTestFile( 'proto_project' ) )

    app.post_json(
      '/run_completer_command',
      BuildRequest(
        filetype = 'proto',
        command_arguments = [ 'StopServer' ]
      )
    )

    request_data = BuildRequest( filetype = 'proto' )
    assert_that( app.post_json( '/debug_info', request_data ).json,
                 has_entry(
                   'completer',
                   has_entry( 'servers', contains_exactly(
                     has_entry( 'is_running', False )
                   ) )
                 ) )
