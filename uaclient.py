#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
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


USAGE = "Usage: python uaclient.py config metodo opcion"

# Cliente UDP simple.

coms = sys.argv

# Comprobamos el número de argumentos

if len(coms) != 4:
    print USAGE
    sys.exit()

# Inicializamos el programa e interpretamos los comandos
METODO = coms[2].capitalize()  # No importa cómo nos introduzcan el método
CONFIG = coms[1]

# Interpretamos el archivo de configuración mediante la clase instanciada"
parser = make_parser()
sHandler = ConfigXMLHandler()
parser.setContentHandler(sHandler)
parser.parse(open(CONFIG))
config = sHandler.get_config()

SERVER_IP = config["uaserver"]["ip"]
SERVER_PORT = config["uaserver"]["puerto"]

RTP_PORT = config["rtpaudio"]["puerto"]

PR_IP = config["regproxy"]["ip"]
PR_PORT = config["regproxy"]["puerto"]

LOG = config["log"]["path"]

AUDIO = config["audio"]["path"]

sys.exit()

def get_fecha():
    fecha = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
    return fecha

def mensaje(metodo):
    """ Devuelve un string con la forma del mensaje a enviar """
    msg = metodo + " sip:" + NOMBRE + "@" + SERVER + " SIP/2.0\r\n"
    return msg


def send(metodo):
    """ Envía al servidor un mensaje usando el método como parámetro """
    msg = mensaje(metodo)
    if metodo != "BYE" and metodo != "INVITE" and metodo != "ACK":
        #Detectamos el error, aunque enviamos igualmente
        print "------WARNING: Método no contemplado"
        print "------    Métodos contemplados: INVITE, BYE, ACK"
    print "Enviando: " + msg
    my_socket.send(msg + '\r\n')


def rcv():
    """ Recibe la respuesta y devuelve el código del protocolo """
    data = my_socket.recv(1024)
    print 'Recibido -- ', data
    return data

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    my_socket.connect((SERVER, int(PORT)))
except socket.gaierror:  # Cuando la IP es inválida
    print "Error: No server listening at" + IP + "port" +  PORT
    print USAGE
    sys.exit()
except ValueError:  # Cuando el puerto no es un número
    print "Error: invalid port"
    print USAGE
    sys.exit()

send(METODO)  # Enviamos el metodo con el que nos llaman

try:
    data = rcv()
except socket.error:  # Cuando el servidor no existe
    print "Error: No server listening at",
    print SERVER + " port " + PORT
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
    print "El servidor no entiende el método " + METODO
elif code == "405":          # Method Not Allowed
    print "Error en el servidor: Método no contemplado"
elif code == "200":          # Sucederá cuando enviemos un BYE
    if METODO == "BYE":
        print "Conexión finalizada con éxito"
else:
    print "MEGABRUTALFATAL ERROR: Respuesta no contemplada"


print "Terminando socket..."

# Cerramos todo
my_socket.close()
print "Fin."
