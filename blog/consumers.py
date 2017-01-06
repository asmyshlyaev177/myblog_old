from channels import Group
from channels.sessions import channel_session


# Connected to websocket.connect
@channel_session
def ws_add(message):
    path = message.content['path'].strip('/').split('/')[-1]
    print("************************")
    print(str(path))

    Group(path).add(message.reply_channel)


# Connected to websocket.receive
@channel_session
def ws_message(message):
    print("**********ONMESSAGE**************")
    print(str(message.content['path'].strip('/').split('/')[-1]))
    print("**********TEXT**************")
    print(str(message.content['text']))

    group = message.content['path'].strip('/').split('/')[-1]
    Group(group).send({
        # "text": "[user] %s" % message.content['text'],
        "text": message.content['text'],
    })


# Connected to websocket.disconnect
@channel_session
def ws_disconnect(message):
    group = message.content['path'].strip('/').split('/')[-1]
    Group(group).discard(message.reply_channel)
