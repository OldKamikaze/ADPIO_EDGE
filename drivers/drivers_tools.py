import ujson


def connect_id_gen(src, net, dev_id, obj_id):
    return f"{src}[{net}]::({dev_id})::{obj_id}"


def connect_id_gen_jsn(jsn):
    return f"{jsn['src']}[{jsn['net']}]::({jsn['device_id']})::{jsn['object_id']}"


#BACnet_IP[6630:1]::(877001)::analog-input,1
def connect_id_decode(id_str):
    src    = id_str[                         :  id_str.index('[')    ]
    net    = id_str[id_str.index('[')    + 1 :  id_str.index(']::(') ]
    dev_id = id_str[id_str.index(']::(') + 4 :  id_str.index(')::')  ]
    obj_id = id_str[id_str.index(')::')  + 3 :                       ]

    return src, net, dev_id, obj_id


def connect_id_decode_jsn(id_str):
    if id_str == '': return None
    try:
        src, net, dev_id, obj_id = connect_id_decode(id_str)
        return { "src": src, "net": net, "device_id": dev_id, "object_id": obj_id }
    except Exception as ex:
        print(f"Build Network Error: Connector failed do decode '{id_str}' : {ex}")
        return None    