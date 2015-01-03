#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class ConfigXMLHandler(ContentHandler):

    def __init__(self):

        self.config = {}

    def startElement(self, name, attrs):

        if name == 'account':
            # De esta manera tomamos los valores de los atributos
            account = {}
            account['username'] = attrs.get('username', "")
            account['passwd'] = attrs.get('passwd', "")

            self.config["account"] = account

        elif name == 'uaserver':

            uaserver = {}
            uaserver['ip'] = attrs.get('ip', "")
            uaserver['puerto'] = attrs.get('puerto', "")

            self.config["uaserver"] = uaserver

        elif name == 'rtpaudio':

            rtpaudio = {}
            rtpaudio['puerto'] = attrs.get('puerto', "")

            self.config["rtpaudio"] = rtpaudio

        elif name == 'regproxy':

            regproxy = {}
            regproxy['ip'] = attrs.get('ip', "")
            regproxy['puerto'] = attrs.get('puerto', "")

            self.config["regproxy"] = regproxy

        elif name == 'log':

            log = {}
            log['path'] = attrs.get('path', "")

            self.config["log"] = log

        elif name == 'audio':

            audio = {}
            audio['path'] = attrs.get('path', "")

            self.config["audio"] = audio

    def get_config(self):
        return self.config


USAGE = "Usage: python uaclient.py config method option"

# Cliente UDP simple.

coms = sys.argv

# Comprobamos el número de argumentos

if len(coms) != 4:
    print USAGE
    sys.exit()

# Inicializamos el programa e interpretamos los comandos
CONFIG = coms[1]
METHOD = coms[2].capitalize()  # No importa cómo nos introduzcan el método
OPTION = coms[3]

# Interpretamos el archivo de configuración mediante la clase instanciada"
parser = make_parser()
sHandler = ConfigXMLHandler()
parser.setContentHandler(sHandler)
parser.parse(open(CONFIG))
config = sHandler.get_config()

NAME = config["account"]["username"]
PASS = config["account"]["passwd"]

if config["uaserver"]["ip"] != "":
    SERVER_IP = config["uaserver"]["ip"]
else:
    SERVER_IP = "127.0.0.1"
SERVER_PORT = int(config["uaserver"]["puerto"])

RTP_PORT = int(config["rtpaudio"]["puerto"])

PR_IP = config["regproxy"]["ip"]
PR_PORT = int(config["regproxy"]["puerto"])

LOGPATH = config["log"]["path"]

AUDIO = config["audio"]["path"]

def get_fecha():
    fecha = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
    return fecha

def log(msg):
    msg = " ".join(msg.split("\r\n")) #Sustituimos los saltos de linea
    msg = get_fecha() + " " + msg + "\r\n"
    fich.write(msg)

def mensaje(metodo, add):
    """ Devuelve un string con la forma del mensaje a enviar """
    msg = metodo + " sip:" + add + " SIP/2.0\r\n"
    return msg


def send(metodo):
    """ Envía al servidor un mensaje usando el método como parámetro """
    if metodo == "Register":
        add = NAME + ":" + SERVER_PORT
        msg = mensaje(metodo, add)
        msg += "Expires: " + OPTION + "\r\n"
    else:
        msg = mensaje(metodo, OPTION)    
        if metodo == "Invite":
            msg += "Content-Type: application/sdp\r\n\r\n"
            msg += "v=o\r\n"                                  #v
            msg += "o=" + NAME + " " + SERVER_IP + "\r\n"     #o
            msg += "s=sesionchachi\r\n"                       #s
            msg += "t=0\r\n"                                  #t
            msg += "m=audio " + str(RTP_PORT) + " RTP\r\n"    #m

    print "Enviando: " + msg
    my_socket.send(msg + '\r\n')

    # Registramos en el log:
    logmsg = "Sent to " + PR_IP + ":" + str(PR_PORT) + ": " + msg
    log(logmsg)


def rcv():
    """ Recibe la respuesta """
    data = my_socket.recv(1024)
    print 'Recibido -- ', data
    return data

def end():
    # Cerramos todo
    log("Finishing")
    my_socket.close()
    fich.close
    print "Byee!!!"


# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
fich = open(LOGPATH, "w") # Abrimos el archivo de log
log("Starting...\r\n")
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Nos conectamos al sevidor (proxy) y le enviamos el mensaje
try:
    my_socket.connect((PR_IP, PR_PORT))
except socket.gaierror:  # Cuando la IP es inválida
    error = "Error: No server listening at" + PR_IP + " port " +  str(PR_PORT)
    log(error)
    print error
    print USAGE
    end()
    sys.exit()
except ValueError:  # Cuando el puerto no es un número
    error = "Error: invalid port"
    log(error)
    print error
    print USAGE
    end()
    sys.exit()

send(METHOD)  # Enviamos según el metodo con el que nos llaman


# Esperamos la respuesta del servidor
try:
    data = rcv()
except socket.error:  # Cuando el servidor no existe
    error = "Error: No server listening at " + PR_IP + " port " + str(PR_PORT)
    log(error)
    print error
    end()
    sys.exit()
except KeyboardInterrupt:
    end()
    sys.exit()

code = data.split()[1]

if code == "100":
# Trying, buscamos recibir Ring y Ok, en esta práctica en el mismo mensaje
    data = data.split("\r\n\r\n")
    if data[1].split()[1] == "180":      # Trying
        if data[2].split()[1] == "200":  # OK
            send("ACK")
        else:
            print "Error: OK no recibido"
    else:
        print "Error: Trying no recibido"

elif code == "400":          # Bad Request
    print "El servidor no entiende el método " + METHOD
elif code == "405":          # Method Not Allowed
    print "Error en el servidor: Método no contemplado"
elif code == "200":          # Sucederá cuando enviemos un BYE
    if METHOD == "BYE":
        print "Conexión finalizada con éxito"
else:
    print "MEGABRUTALFATAL ERROR: Respuesta no contemplada"

print "Terminando socket..."

end()
