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

from unittest import TestCase
from unittest.mock import patch
from hamcrest import assert_that, equal_to, not_none, none

from ycmd import user_options_store
from ycmd.completers.proto.hook import GetCompleter
from ycmd.completers.proto.proto_completer import ProtoCompleter


class ProtoCompleterTest( TestCase ):
  """Tests for ProtoCompleter loading and configuration."""

  def test_GetCompleter_BuflsFound( self ):
    """GetCompleter returns a ProtoCompleter when bufls is available."""
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/usr/local/bin/bufls' ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer, not_none() )
      assert_that( isinstance( completer, ProtoCompleter ), equal_to( True ) )


  def test_GetCompleter_BuflsNotFound( self ):
    """GetCompleter returns None when bufls is not installed."""
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                None ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer, none() )


  def test_GetCompleter_BuflsFromUserOption( self ):
    """bufls_binary_path user option is preferred over PATH lookup."""
    custom_bufls = '/custom/path/to/bufls'
    with patch( 'ycmd.utils.FindExecutableWithFallback',
                wraps = lambda x, fb: x if x == custom_bufls else None ):
      user_options = user_options_store.GetAll().copy(
          bufls_binary_path = custom_bufls )
      completer = GetCompleter( user_options )
      assert_that( completer, not_none() )
      assert_that( completer._bufls_path, equal_to( custom_bufls ) )


  def test_GetCompleter_UserOptionOverridesDefault( self ):
    """bufls_binary_path takes precedence over a found BUFLS_EXECUTABLE."""
    user_path = '/user/specified/bufls'
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/default/bufls' ):
      with patch( 'ycmd.utils.FindExecutableWithFallback',
                  return_value = user_path ):
        user_options = user_options_store.GetAll().copy(
            bufls_binary_path = user_path )
        completer = GetCompleter( user_options )
        assert_that( completer._bufls_path, equal_to( user_path ) )


  def test_GetCompleter_EmptyUserOption_FallsBackToDefault( self ):
    """Empty bufls_binary_path falls back to the discovered BUFLS_EXECUTABLE."""
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/usr/bin/bufls' ):
      with patch( 'ycmd.utils.FindExecutableWithFallback',
                  return_value = '/usr/bin/bufls' ) as mock_find:
        GetCompleter( user_options_store.GetAll() )
        # Verify FindExecutableWithFallback was called with the default
        args, _ = mock_find.call_args
        assert_that( args[ 1 ], equal_to( '/usr/bin/bufls' ) )


  def test_SupportedFiletypes( self ):
    """ProtoCompleter only activates for proto filetype."""
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/usr/local/bin/bufls' ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer.SupportedFiletypes(), equal_to( [ 'proto' ] ) )


  def test_GetServerName( self ):
    """Server name is 'bufls' for display in debug info."""
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/usr/local/bin/bufls' ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer.GetServerName(), equal_to( 'bufls' ) )


  def test_GetCommandLine( self ):
    """Command line uses 'serve' subcommand as required by bufls."""
    bufls_path = '/usr/local/bin/bufls'
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                bufls_path ):
      with patch( 'ycmd.utils.FindExecutableWithFallback',
                  return_value = bufls_path ):
        completer = GetCompleter( user_options_store.GetAll() )
        assert_that( completer.GetCommandLine(),
                     equal_to( [ bufls_path, 'serve' ] ) )


  def test_GetProjectRootFiles( self ):
    """Project root detection recognizes both buf.yaml and buf.work.yaml."""
    with patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE',
                '/usr/local/bin/bufls' ):
      completer = GetCompleter( user_options_store.GetAll() )
      root_files = completer.GetProjectRootFiles()
      assert_that( 'buf.yaml' in root_files, equal_to( True ) )
      assert_that( 'buf.work.yaml' in root_files, equal_to( True ) )


  @patch( 'ycmd.completers.proto.proto_completer.BUFLS_EXECUTABLE', None )
  @patch( 'ycmd.completers.proto.proto_completer.utils' )
  def test_GetCompleter_LogsWhenBuflsNotFound( self, mock_utils ):
    """A warning is logged when bufls cannot be found."""
    mock_utils.FindExecutableWithFallback.return_value = None
    mock_utils.LOGGER = __import__( 'logging' ).getLogger( __name__ )

    # ShouldEnableProtoCompleter returns False → GetCompleter returns None
    with patch( 'ycmd.completers.proto.proto_completer.ShouldEnableProtoCompleter',
                return_value = False ):
      result = GetCompleter( user_options_store.GetAll() )
      assert_that( result, none() )
