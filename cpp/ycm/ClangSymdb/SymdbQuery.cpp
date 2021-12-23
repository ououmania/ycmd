#include "SymdbQuery.h"
#include "Session.h"

namespace symdb {

static const std::string kDefaultSockPath = "/tmp/symdb.sock";

bool IsWantedCursor(CXCursor cursor) {
    auto kind = clang_getCursorKind(cursor);
    switch (kind) {
    case CXCursorKind::CXCursor_CXXMethod:
    case CXCursorKind::CXCursor_Constructor:
    case CXCursorKind::CXCursor_Destructor:
    case CXCursorKind::CXCursor_DeclRefExpr:
        return true;

    case CXCursorKind::CXCursor_StructDecl:
    case CXCursorKind::CXCursor_TypedefDecl:
    case CXCursorKind::CXCursor_TypeAliasDecl:
    case CXCursorKind::CXCursor_FunctionTemplate:
    case CXCursorKind::CXCursor_FunctionDecl:
    case CXCursorKind::CXCursor_VarDecl:
        return clang_Cursor_getStorageClass(cursor) != CX_StorageClass::CX_SC_Static;

    default:
        return false;
    }
}

Location GetDefinitionLocation(const std::string &project_name, CXCursor cursor)
{
    if (project_name.empty()) {
        return Location {};
    }

    if (!IsWantedCursor(cursor)) {
        return Location {};
    }

    std::string usr = YouCompleteMe::CXStringToString(clang_getCursorUSR(cursor));
    if (usr.empty()) {
        return Location {};
    }

    Location cursor_loc (clang_getCursorLocation(cursor));

    symdb::Session session { symdb::kDefaultSockPath };

    return session.GetSymbolDefinition(project_name, usr, cursor_loc.filename_);
}

std::vector<Location> GetReferenceLocation(const std::string &project_name, CXCursor cursor)
{
    Location cursor_loc (clang_getCursorLocation(cursor));

    std::string usr = YouCompleteMe::CXStringToString(clang_getCursorUSR(cursor));
    if (usr.empty()) {
        usr = YouCompleteMe::CXStringToString(clang_getCursorDisplayName(cursor));
    }

    if (usr.empty()) {
        return std::vector<Location> {};
    }

    symdb::Session session { symdb::kDefaultSockPath };

    return session.GetSymbolReferences(project_name, usr, cursor_loc.filename_);
}

} // symdb
