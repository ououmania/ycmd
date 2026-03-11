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

from ycmd import utils
from ycmd.completers.language_server import language_server_completer


# bufls installed by build.py --proto-completer lands in third_party/go/bin/,
# the same location as gopls.
PATH_TO_BUFLS = os.path.abspath( os.path.join( os.path.dirname( __file__ ),
  '..', '..', '..', 'third_party', 'go', 'bin',
  utils.ExecutableName( 'bufls' ) ) )


def ShouldEnableProtoCompleter( user_options ):
  path = user_options[ 'bufls_binary_path' ]
  server = utils.FindExecutableWithFallback( path, PATH_TO_BUFLS )
  if server:
    return True
  utils.LOGGER.info( 'Not enabling proto completer: bufls not found. '
                     'Install with: python build.py --proto-completer' )
  return False


class ProtoCompleter( language_server_completer.LanguageServerCompleter ):
  def __init__( self, user_options ):
    super().__init__( user_options )
    path = user_options[ 'bufls_binary_path' ]
    self._bufls_path = utils.FindExecutableWithFallback( path, PATH_TO_BUFLS )


  def GetServerName( self ):
    return 'bufls'


  def GetCommandLine( self ):
    return [ self._bufls_path, 'serve' ]


  def GetProjectRootFiles( self ):
    # buf.yaml marks the root of a buf module / proto project.
    # Also support plain proto projects without buf.
    return [ 'buf.yaml', 'buf.work.yaml' ]


  def SupportedFiletypes( self ):
    return [ 'proto' ]
