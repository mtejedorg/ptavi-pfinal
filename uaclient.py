#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys

USAGE = "Usage: python client.py method receiver@IP:SIPport"

# Cliente UDP simple.

coms = sys.argv

# Comprobamos el número de argumentos

if len(coms) != 3:
    print USAGE
    sys.exit()

# Inicializamos el programa e interpretamos los comandos
METODO = coms[1].upper()  # Nos pueden pasar el parámetro en minúsculas
servidor = coms[2]
datos = servidor.split("@")
NOMBRE = datos[0]
direccion = datos[1].split(":")
SERVER = direccion[0]
PORT = direccion[1]


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
    print "Error: invalid IP"
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
