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

import os
import shutil

from ycmd import utils
from ycmd.completers.language_server import language_server_completer
from ycmd.completers.language_server import language_server_protocol as lsp
from ycmd.completers.language_server.language_server_completer import (
  _LspSymbolListToGoTo,
  REQUEST_TIMEOUT_COMMAND )


# LSP SymbolKind values for child-level (member) symbols.
_CHILD_SYMBOL_KINDS = {
  8,   # Field
  23,  # EnumMember
}


def _FilterSymbols( query, symbols ):
  """If there are top-level symbols (message/enum/service) whose name exactly
  matches the query, return only those and filter out child-level members.
  Otherwise return all symbols unfiltered (the user is searching for a field
  or enum member)."""
  exact_top_level = [ s for s in symbols
                      if s[ 'name' ] == query
                      and s[ 'kind' ] not in _CHILD_SYMBOL_KINDS ]
  if exact_top_level:
    return exact_top_level
  return symbols


# buf CLI with built-in LSP (replaces deprecated bufls).
# Fall back to bufls for backward compatibility.
PATH_TO_BUFLS = os.path.abspath( os.path.join( os.path.dirname( __file__ ),
  '..', '..', '..', 'third_party', 'go', 'bin',
  utils.ExecutableName( 'bufls' ) ) )


def _FindBuf( user_options ):
  """Find buf or bufls binary. Prefer buf (has built-in LSP), fall back to
  legacy bufls."""
  # 1. User-configured path (bufls_binary_path option)
  user_path = user_options[ 'bufls_binary_path' ]
  if user_path:
    server = utils.FindExecutableWithFallback( user_path, None )
    if server:
      return server

  # 2. buf CLI on PATH (has built-in LSP since v1.50+)
  buf_path = shutil.which( 'buf' )
  if buf_path:
    return buf_path

  # 3. Legacy bufls in third_party
  server = utils.FindExecutableWithFallback( '', PATH_TO_BUFLS )
  if server:
    return server

  return None


def ShouldEnableProtoCompleter( user_options ):
  server = _FindBuf( user_options )
  if server:
    return True
  utils.LOGGER.info( 'Not enabling proto completer: buf/bufls not found. '
                     'Install buf CLI or run: python build.py '
                     '--proto-completer' )
  return False


class ProtoCompleter( language_server_completer.LanguageServerCompleter ):
  def __init__( self, user_options ):
    super().__init__( user_options )
    self._buf_path = _FindBuf( user_options )
    self._buf_name = os.path.basename( self._buf_path )


  def GetServerName( self ):
    return 'buf-lsp'


  def GetCommandLine( self ):
    # buf CLI: `buf lsp serve`
    # legacy bufls: `bufls serve`
    if self._buf_name.startswith( 'buf' ) and 'bufls' not in self._buf_name:
      return [ self._buf_path, 'lsp', 'serve' ]
    return [ self._buf_path, 'serve' ]


  def GetProjectRootFiles( self ):
    # buf.yaml marks the root of a buf module / proto project.
    return [ 'buf.yaml', 'buf.work.yaml' ]


  def SupportedFiletypes( self ):
    return [ 'proto' ]


  def GoToSymbol( self, request_data, args ):
    if not self.ServerIsReady():
      raise RuntimeError( 'Server is initializing. Please wait.' )

    self._UpdateServerWithFileContents( request_data )

    if len( args ) < 1:
      raise RuntimeError( 'Must specify something to search for' )

    query = args[ 0 ]

    request_id = self.GetConnection().NextRequestId()
    response = self.GetConnection().GetResponse(
      request_id,
      lsp.WorkspaceSymbol( request_id, query ),
      REQUEST_TIMEOUT_COMMAND )

    result = response.get( 'result' ) or []
    result = _FilterSymbols( query, result )
    return _LspSymbolListToGoTo( request_data, result )
