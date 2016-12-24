from channels import Group

# Connected to websocket.connect
def ws_add(message):
    path = message.content['path'].strip('/').split('/')[-1]
    print("************************")
    print(str(path))

    Group(path).add(message.reply_channel)

# Connected to websocket.receive
def ws_message(message):
    print("**********ONMESSAGE**************")
    print(str(message.content['path'].strip('/').split('/')[-1]))
    print("**********TEXT**************")
    print(str(message.content['text']))

    group = message.content['path'].strip('/').split('/')[-1]
    Group(group).send({
        #"text": "[user] %s" % message.content['text'],
        "text":  message.content['text'],
    })

# Connected to websocket.disconnect
def ws_disconnect(message):
    group = message.content['path'].strip('/').split('/')[-1]
    Group(group).discard(message.reply_channel)
