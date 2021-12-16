#ifndef SESSION_H_W5DAS4RL
#define SESSION_H_W5DAS4RL

#include "ClangCompleter/Location.h"
#include <memory>
#include <vector>

namespace google {

namespace protobuf {
    class Message;
} // protobuf

} // google

namespace symdb {

using YouCompleteMe::Location;

class Session
{
public:
    explicit Session(const std::string &path);
    ~Session();

    Location GetSymbolDefinition(const std::string &proj_name,
                                 const std::string &symbol,
                                 const std::string &abs_path);

    std::vector<Location> GetSymbolReferences(const std::string &proj_name,
                                              const std::string &symbol,
                                              const std::string &abs_path);

private:
    bool Connect(const std::string &path);

    bool send(int msg_id, const google::protobuf::Message &body);

    template <class ReplyType>
    bool SendRequestAndGetReply(int msg_id, const google::protobuf::Message &req,
        ReplyType &rsp);

private:
    int fd_;
};

} // symdb

#endif /* end of include guard: SESSION_H_W5DAS4RL */
