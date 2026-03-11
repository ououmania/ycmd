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

  @patch( 'shutil.which', return_value = '/usr/local/bin/buf' )
  def test_GetCompleter_BufFound( self, *args ):
    """GetCompleter returns a ProtoCompleter when buf is available."""
    completer = GetCompleter( user_options_store.GetAll() )
    assert_that( completer, not_none() )
    assert_that( isinstance( completer, ProtoCompleter ), equal_to( True ) )


  @patch( 'shutil.which', return_value = None )
  def test_GetCompleter_BufNotFound( self, *args ):
    """GetCompleter returns None when buf is not installed."""
    completer = GetCompleter( user_options_store.GetAll() )
    assert_that( completer, none() )


  def test_SupportedFiletypes( self ):
    """ProtoCompleter only activates for proto filetype."""
    with patch( 'shutil.which', return_value = '/usr/local/bin/buf' ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer.SupportedFiletypes(), equal_to( [ 'proto' ] ) )


  def test_GetServerName( self ):
    """Server name is 'buf-lsp' for display in debug info."""
    with patch( 'shutil.which', return_value = '/usr/local/bin/buf' ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer.GetServerName(), equal_to( 'buf-lsp' ) )


  def test_GetCommandLine( self ):
    """Command line uses 'buf lsp serve'."""
    buf_path = '/usr/local/bin/buf'
    with patch( 'shutil.which', return_value = buf_path ):
      completer = GetCompleter( user_options_store.GetAll() )
      assert_that( completer.GetCommandLine(),
                   equal_to( [ buf_path, 'lsp', 'serve' ] ) )


  def test_GetProjectRootFiles( self ):
    """Project root detection recognizes both buf.yaml and buf.work.yaml."""
    with patch( 'shutil.which', return_value = '/usr/local/bin/buf' ):
      completer = GetCompleter( user_options_store.GetAll() )
      root_files = completer.GetProjectRootFiles()
      assert_that( 'buf.yaml' in root_files, equal_to( True ) )
      assert_that( 'buf.work.yaml' in root_files, equal_to( True ) )


  @patch( 'shutil.which', return_value = None )
  @patch( 'ycmd.completers.proto.proto_completer.utils' )
  def test_GetCompleter_LogsWhenBufNotFound( self, mock_utils, *args ):
    """A warning is logged when buf cannot be found."""
    mock_utils.LOGGER = __import__( 'logging' ).getLogger( __name__ )

    with patch( 'ycmd.completers.proto.proto_completer.ShouldEnableProtoCompleter',
                return_value = False ):
      result = GetCompleter( user_options_store.GetAll() )
      assert_that( result, none() )
