from channels import Group
from channels.sessions import channel_session
import json
from django.utils.encoding import uri_to_iri

# Connected to websocket.connect
@channel_session
def ws_add(message):
    path = uri_to_iri(message.content['path'].strip('/').split('/')[-1]) 
    #.split('-')[-1])
    #print("************************")
    #print(str(path))
    #print("************************")
    hello = {'hello': 1}
    message.reply_channel.send({
        "text": json.dumps(hello),
    })
    Group(path).add(message.reply_channel)


# Connected to websocket.receive
@channel_session
def ws_message(message):
    # print("**********ONMESSAGE**************")
    # print(str(message.content['path'].strip('/').split('/')[-1]))
    #print("**********TEXT**************")
    #print(str(message.content['text']))

    group = uri_to_iri(message.content['path'].strip('/').split('/')[-1] )
    #.split('-')[-1])
    Group(group).send({
        "text": message.content['text'],
    })


# Connected to websocket.disconnect
@channel_session
def ws_disconnect(message):
    group = uri_to_iri(message.content['path'].strip('/').split('/')[-1]) 
    #.split('-')[-1])
    Group(group).discard(message.reply_channel)
