#ifndef SYMDBQUERY_H_SU580CG7
#define SYMDBQUERY_H_SU580CG7

#include <vector>
#include <memory>
#include "ClangCompleter/Location.h"

namespace symdb {
  using YouCompleteMe::Location;

  Location GetDefinitionLocation(const std::string &project_name, CXCursor cursor);

  std::vector<Location> GetReferenceLocation(const std::string &project_name, CXCursor cursor);
} // symdb

#endif /* end of include guard: SYMDBQUERY_H_SU580CG7 */
