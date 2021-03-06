#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco
en UDP simple
"""

import SocketServer
import socket
import sys
import time
import random
import string
from uaclient import log
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

clients = {}


class ConfigXMLHandler(ContentHandler):

    def __init__(self):

        self.config = {}

    def startElement(self, name, attrs):

        if name == 'server':
            # De esta manera tomamos los valores de los atributos
            server = {}
            server['name'] = attrs.get('name', "")
            server['ip'] = attrs.get('ip', "")
            server['puerto'] = attrs.get('puerto', "")

            self.config["server"] = server

        elif name == 'database':

            database = {}
            database['path'] = attrs.get('path', "")
            database['passwdpath'] = attrs.get('passwdpath', "")

            self.config["database"] = database

        elif name == 'log':

            log = {}
            log['path'] = attrs.get('path', "")

            self.config["log"] = log

    def get_config(self):
        return self.config


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    SIP Register server class

    Métodos (más detallados en el propio método:
        register2file: crea un archivo con los clientes
        register: se encarga de procesar los mensajes register
    """
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def register2file(self):
        """
        Imprime la lista de clientes en el archivo 'registered.txt',
        con el formato:

        User \t IP \t Port \t Expires(s) \t Timeremaining(s)
        """
        fich = open(DATABASE, 'w')
        info = "User \t IP \t Port \t Expires \t Remaining\r\n"
        for client in clients:
            info += client + " \t "
            info += clients[client]["IP"] + " \t "
            info += clients[client]["port"] + " \t "
            tiempo = clients[client]["time"]
            info += str(tiempo) + " \t "
            remaining = tiempo - time.time()
            info += str(remaining)
            info += "\r\n"
        fich.write(info)
        fich.close()

    def find(self, name):
        """
        Encuentra al cliente en cuestión. Si está en la lista, devuelve
        IP y puerto, en caso contrario devuelve ""
        """
        ep = ""
        for client in clients:
            if client == name:
                clip = clients[client]["IP"]
                clport = clients[client]["port"]
                ep = clip + ":" + clport
                break
        return ep

    def checksdp(self, sdp):
        val = True
        for linea in sdp:
            if linea[:2] == "v=" or linea[:2] == "t=":
                try:
                    int(linea[2:3])
                except ValueError:
                    val = False

    def checkrequest(self, palabras):
        """
        Comprueba si son correctos los mensajes del tipo:
            Método sip:nombre@dirección SIP/versión
        """
        val = True
        val = val and palabras[1].split(":")[0] == "sip"
        val = val and palabras[1].split("@")[0] != ""
        val = val and palabras[1].split("@")[1] != ""
        val = val and palabras[2].split("/")[0] == "SIP"
        val = val and float(palabras[2].split("/")[1]) <= 2.0
        return val

    def randomstring(self, upp, low, dig, length):
        """
        Uso: upp, low, dig funcionan como booleanos.
        Se deben instanciar como True, False, 1 o 0.
        El uso de otro entero funciona pero no es eficiente.

        Length nos da la longitud del string aleatorio
        """
        available = upp * string.ascii_uppercase
        available += low * string.ascii_lowercase
        available += dig * string.digits
        rs = ""

        if available != "":
            for i in range(length):
                rs += random.SystemRandom().choice(available)

        return rs

    def headed(self, msg):
        head = "Via: SIP/2.0/UDP "
        head += str(IP) + ":" + str(PORT)
        branch = ";branch="
        branch += self.randomstring(1, 1, 1, 9)
        head += branch + "\r\n"

        req = msg.split("\r\n")[0] + "\r\n"
        reqlen = len(req)
        add = msg[reqlen:]
        res = req + head + add

        return res

    def checkanswer(self, palabras):
        """
        Comprueba si son correctos los mensajes del tipo:
            SIP/versión código Método
        """
        val = True
        val = val and palabras[0].split("/")[0] == "SIP"
        val = val and float(palabras[0].split("/")[1]) <= 2.0
        metodo = palabras[2]
        try:
            code = int(palabras[1])
            val = val and (code == 100 and metodo == "Trying")
            val = val and (code == 180 and metodo == "Ringing")
            val = val and (code == 200 and metodo == "OK")
            val = val and (code == 400 and metodo == "Bad Request")
            val = val and (code == 404 and metodo == "User Not Found")
            val = val and (code == 405 and metodo == "Method Not Allowed")
        except ValueError:
            val = False
        return val

    def manage(self, line):
        """
        Si es un mensaje register, agrega al cliente en cuestión
        a la variable global 'clients', informando por pantalla
        de cada paso.
        Guarda cada cliente como un diccionario del tipo
        Cliente:
            Nombre, un string generalmente de la forma nombre@dominio.com
            Valores:
                IP, un string con la IP del cliente
                time: segundo desde el 1 de enero de 1979 en el
                cual expirará
        Si no es un mensaje register,
        reenviará el mensaje a quien esté dirigido,
        siguiendo el protocolo adecuado.
        """
        lineas = line.split("\r\n")
        palabras = lineas[0].split(" ") + lineas[1].split(" ")

        condition = palabras[0] == "INVITE"
        condition = condition or palabras[0] == "ACK"
        condition = condition or palabras[0] == "BYE"

        rightsdp = True
        if palabras[0] == "INVITE":
            rightsdp = self.checksdp(lineas)

        if self.checkrequest(palabras) or not rightsdp:
            if palabras[0] == "REGISTER":
                cliente = palabras[1].split(":")[1]
                #prot_ver es una lista que incluye protocolo y versión
                prot_ver = palabras[2].split("/")
                Data = prot_ver[0] + "/" + prot_ver[1] + " 200 OK\r\n\r\n"
                expires = int(palabras[4])

                print "Registrando cliente nuevo..."
                time_act = time.time() + expires
                clip = self.client_address[0]
                clport = palabras[1].split(":")[2]

                valor = {"IP": clip, "port": clport, "time": time_act}
                clients[cliente] = valor
                print "...cliente agregado: ",
                print cliente + ": ",
                print valor

                logmsg = "Registered client " + cliente
                logmsg += valor['IP'] + ":" + str(self.client_address[1])
                log(logmsg, fich)

                if expires == 0:
                    print "El tiempo de expiración es 0.",
                    del clients[cliente]
                    print "El cliente '" + cliente + "' ha sido borrado"
                logmsg = "Sent to " + clip + ":" + clport + ": " + Data
                log(logmsg, fich)
                self.wfile.write(Data)

            elif condition:
                name = palabras[1].split(":")[1]
                ep = self.find(name)
                print "Encontrado " + ep
                if ep != "":  # Si tenemos al cliente registrado
                    clip = ep.split(":")[0]
                    clport = ep.split(":")[1]
                    self.my_socket.connect((clip, int(clport)))
                    line = self.headed(line)
                    print "Enviamos:\r\n" + line
                    self.my_socket.send(line)
                    answer = self.my_socket.recv(1024)
                    print 'Recibido:\r\n', answer
                    logmsg = "Received from " + clip + ":"
                    logmsg += str(clport) + ": " + answer
                    log(logmsg, fich)
                    answer = self.headed(answer)
                    self.wfile.write(answer)

                    clip = self.client_address[0]
                    clport = self.client_address[1]
                    logmsg = "Sent to " + clip + ":"
                    logmsg += str(clport) + ": " + answer
                    log(logmsg, fich)
                else:
                    prot_ver = palabras[2].split("/")
                    Data = prot_ver[0] + "/" + prot_ver[1]
                    Data += " 404 User Not Found\r\n\r\n"
                    self.wfile.write(Data)
            else:
                prot_ver = palabras[2].split("/")
                Data = prot_ver[0] + "/" + prot_ver[1]
                Data += " 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(Data)
        else:
                cliente = palabras[1].split(":")[1]
                #prot_ver es una lista que incluye portocolo y versión
                prot_ver = palabras[2].split("/")
                Data = prot_ver[0] + "/" + prot_ver[1]
                Data += " 400 Bad Request\r\n\r\n"
                self.wfile.write(Data)

    def update(self):
        """ Actualiza la lista de clientes a la hora actual"""
        lista_tmp = []  # Para guardar qué clientes (key) debemos borrar
        for client in clients:
            if clients[client]["time"] < time.time():
                lista_tmp.append(client)
        for client in lista_tmp:
            print "\r\n>> Lista de clientes actualizada:",
            del clients[client]
            print "El cliente '" + client,
            print "' ha sido borrado (su sesión ha expirado)"

    def handle(self):
        """
        Entra en un bucle infinito a la espera de mensajes de clientes.
        Cuando llega un mensaje llama a los procesos correspondientes
        """
        print "Dirección del cliente: ",
        print self.client_address
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            # Asumo que el mensaje REGISTER estará bien construido
            line = self.rfile.read()
            if not line:
                break

            logmsg = "Received from " + self.client_address[0] + ":"
            logmsg += str(self.client_address[1]) + ": " + line
            log(logmsg, fich)
            print line

            self.manage(line)
            self.update()
            self.register2file()

            print "\r\n\r\n>> A la espera de nuevos clientes...\r\n\r\n"

USAGE = "Usage: python proxy_registrar.py config"


def checkip(ip):
    """
    Comprueba que la IP esté formada por 4 valores válidos
    La variable ip debe ser un string
    """
    val = True
    campos = ip.split(".")
    if len(campos) != 4:
        val = False
    for campo in campos:
        condition = int(campo) >= 0
        condition = condition and int(campo) < 256
        if not condition:
            val = False

def recuperarclientes():
    """
    Abre el archivo 'registered.txt' en busca de clientes
    """
    fich = open(DATABASE, 'r')
    for linea in fich:
        head = "User \t IP \t Port \t Expires \t Remaining\r\n"
        condition = linea != head
        condition = condition and linea != ""
        if condition:
            info = linea.split(" \t ")
            user = info[0]
            clip = info[1]
            clport = info[2]
            time = float(info[3])
            valor = {"IP": clip, "port": clport, "time": time}
            clients[user] = valor
    fich.close()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print USAGE
        sys.exit()

    # Creamos un objeto de la clase ConfigXMLHandler
    CONFIGFILE = sys.argv[1]
    xmlHandler = ConfigXMLHandler()
    parser = make_parser()
    parser.setContentHandler(xmlHandler)
    parser.parse(open(CONFIGFILE))

    # Extraemos la información de nuestro diccionario
    config = xmlHandler.get_config()

    NAME = config["server"]["name"]
    if config["server"]["ip"] != "":
        IP = config["uaserver"]["ip"]
        if not checkip(IP):
            print "IP incorrecta"
            sys.exit()
    else:
        IP = "127.0.0.1"

    try:
        PORT = int(config["server"]["puerto"])
    except ValueError:
        print "Puerto incorrecto"
        sys.exit()

    DATABASE = config["database"]["path"]
    PASSWDDB = config["database"]["passwdpath"]
    LOGPATH = config["log"]["path"]
    fich = open(LOGPATH, 'a')

    # Creamos servidor de register y proxy y escuchamos
    log("Starting...", fich)
    s = SocketServer.UDPServer((IP, PORT), SIPRegisterHandler)
    print "Recuperando clientes..."
    try:
        recuperarclientes()
    except IOError:
        print "No se ha recuperado ningún cliente"

    print "Lanzando servidor UDP de SIP Register...\r\n\r\n"
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print "\r\nByeeee!!!!"
        #my_socket.close()
        fich.close()
        sys.exit()
