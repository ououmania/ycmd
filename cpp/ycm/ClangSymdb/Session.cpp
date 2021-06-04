#include "Session.h"
#include "Message.pb.h"
#include <google/protobuf/message.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/select.h>
#include <sys/types.h>

namespace {

struct MessageID {
    enum {
        INVALID = 0,
        CREATE_PROJECT_REQ,
        CREATE_PROJECT_RSP,
        UPDATE_PROJECT_REQ,
        UPDATE_PROJECT_RSP,
        DELETE_PROJECT_REQ,
        DELETE_PROJECT_RSP,
        LIST_PROJECT_REQ,
        LIST_PROJECT_RSP,
        COMPILE_FILE_REQ,
        COMPILE_FILE_RSP,
        GET_SYMBOL_DEFINITION_REQ,
        GET_SYMBOL_DEFINITION_RSP,
        GET_SYMBOL_REFERENCES_REQ,
        GET_SYMBOL_REFERENCES_RSP,
        LIST_FILE_SYMBOLS_REQ,
        LIST_FILE_SYMBOLS_RSP,
        MAX_MESSAGE_ID,
    };
};

# pragma pack(push, 1)
struct FixedHeader {
    uint16_t msg_size;
    uint16_t pb_head_size;
};
# pragma pack(pop)

} // annoymous namespace

namespace symdb {

Session::Session(const std::string &path)
    : fd_(-1)
{
    Connect(path);
}

Session::~Session()
{
    if (fd_ != -1) {
        close(fd_);
    }
}

bool Session::Connect(const std::string &path) {
    fd_ = socket(PF_UNIX, SOCK_STREAM, 0);
    if (fd_ < 0) {
        return false;
    }

    int ret = fcntl(fd_, F_SETFL, O_NONBLOCK);
    if (ret < 0) {
        return false;
    }

    // Very simple implementation to make the code independant.
    sockaddr_un address;
    memset(&address, 0, sizeof(struct sockaddr_un));

    address.sun_family = AF_UNIX;
    snprintf(address.sun_path, PATH_MAX, "%s", path.c_str());

    if (connect(fd_, (sockaddr *) &address, sizeof(address)) != 0 &&
        errno != EINPROGRESS) {
        return false;
    }

    fd_set fdset;
    struct timeval tv;

    FD_ZERO(&fdset);
    FD_SET(fd_, &fdset);
    tv.tv_sec = 2;
    tv.tv_usec = 0;

    if (select(fd_ + 1, NULL, &fdset, NULL, &tv) == 1) {
        int so_error;
        socklen_t len = sizeof(so_error);

        getsockopt(fd_, SOL_SOCKET, SO_ERROR, &so_error, &len);
        return so_error == 0;
    }
    return false;
}

bool Session::send(int msg_id, const google::protobuf::Message &body)
{
    MessageHead head;
    head.set_msg_id(msg_id);
    head.set_body_size(body.ByteSizeLong());

    FixedHeader fh;
    fh.pb_head_size = head.ByteSizeLong();
    fh.msg_size = fh.pb_head_size + body.GetCachedSize();

    char buf[8192];
    memcpy(buf, &fh, sizeof(fh));

    int offset = sizeof(fh);
    const int buf_size_int = sizeof(buf);
    if (!head.SerializeToArray(buf + offset, buf_size_int - offset)) {
        return false;
    }

    offset += head.GetCachedSize();
    if (!body.SerializeToArray(buf + offset, buf_size_int - offset)) {
        return false;
    }

    ssize_t total_size = fh.msg_size + sizeof(fh);
    return write(fd_, buf, total_size) == total_size;
}

template <class ReplyType>
bool Session::SendRequestAndGetReply(int msg_id, const google::protobuf::Message &body, ReplyType &rsp)
{
    if (!send(msg_id, body)) {
        return false;
    }

    fd_set fdset;
    FD_ZERO(&fdset);
    FD_SET(fd_, &fdset);

    struct timeval tv;
    tv.tv_sec = 3;
    tv.tv_usec = 0;

    if (select(fd_ + 1, &fdset, NULL, NULL, &tv) < 0) {
        return false;
    }

    if (!FD_ISSET(fd_, &fdset)) {
        return false;
    }

    FixedHeader fh;
    if (read(fd_, &fh, sizeof(fh)) != sizeof(fh) || fh.msg_size == 0) {
        return false;
    }
    std::vector<char> pb_buf(fh.msg_size);
    if (read(fd_, &pb_buf[0], pb_buf.size()) != (ssize_t) pb_buf.size()) {
        return false;
    }
    return rsp.ParseFromArray(&pb_buf[0], pb_buf.size());
}

Location Session::GetSymbolDefinition(const std::string &proj_name,
    const std::string &symbol, const std::string &abs_path)
{
    GetSymbolDefinitionReq req;
    req.set_proj_name(proj_name);
    req.set_symbol(symbol);
    req.set_abs_path(abs_path);

    GetSymbolDefinitionRsp rsp;
    SendRequestAndGetReply(MessageID::GET_SYMBOL_DEFINITION_REQ, req, rsp);

    if (!rsp.error().empty() || rsp.locations().empty()) {
        return Location {};
    }

    const auto &pb_loc = rsp.locations(0);
    return Location ( pb_loc.path(), pb_loc.line(), pb_loc.column() );
}

std::vector<Location> Session::GetSymbolReferences(
    const std::string &proj_name,
    const std::string &symbol,
    const std::string &abs_path)
{
    std::vector<Location> locations;

    GetSymbolReferencesReq req;
    req.set_proj_name(proj_name);
    req.set_symbol(symbol);
    req.set_path(abs_path);

    GetSymbolReferencesRsp rsp;
    SendRequestAndGetReply(MessageID::GET_SYMBOL_REFERENCES_REQ, req, rsp);

    if (rsp.error().empty() && !rsp.locations().empty()) {
        locations.reserve(rsp.locations_size());
        for (const auto &pb_loc : rsp.locations()) {
            locations.emplace_back( pb_loc.path(), pb_loc.line(), pb_loc.column() );
        }
    }

    return locations;
}

} // symdb
