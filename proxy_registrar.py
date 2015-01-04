#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco
en UDP simple
"""

import SocketServer
import sys
import time

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
    def register2file(self):
        """
        Imprime la lista de clientes en el archivo 'registered.txt',
        con el formato:

        User \t IP \t Expires
        luke@polismassa.com \t localhost \t 2013-10-23 10:37:12
        papa@darthwader.com \t localhost \t 2013-10-23 10:21:15
        """
        fich = open("registered.txt", 'w')
        info = "User \t IP \t Expires\r\n"
        for client in clients:
            info += client + " \t "
            info += clients[client]["IP"] + " \t "
            tiempo = time.gmtime(clients[client]["time"])
            str_time = time.strftime('%Y-%m-%d %H:%M:%S', tiempo)
            info += str_time + " \t "
            info += "\r\n"
        fich.write(info)
        fich.close()

    def register(self, line):
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
        """
        lineas = line.split("\r\n")
        palabras = lineas[0].split(" ") + lineas[1].split(" ")
        if palabras[0] == "REGISTER":
            cliente = palabras[1][4:]
            #prot_ver es una lista que incluye portocolo y versión
            prot_ver = palabras[2].split("/")
            Data = prot_ver[0] + "/" + prot_ver[1] + " 200 OK\r\n\r\n"
            expires = int(palabras[4])

            print "Registrando cliente nuevo..."
            time_act = time.time() + expires
            valor = {"IP": self.client_address[0], "time": time_act}
            clients[cliente] = valor
            print "...cliente agregado: ",
            print cliente + ": ",
            print valor

            if expires == 0:
                print "El tiempo de expiración es 0.",
                del clients[cliente]
                print "El cliente '" + cliente + "' ha sido borrado"

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
            print "El cliente '" + client + "' ha sido borrado (su sesión ha expirado)"

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

            print line

            self.register(line)
            self.update()
            self.register2file()

            print "\r\n\r\n>> A la espera de nuevos clientes...\r\n\r\n"

USAGE = "Usage: python proxy_registrar.py config"

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
    else:
        IP = "127.0.0.1"
    PORT = int(config["server"]["puerto"])

    DATABASE = config["database"]["path"]
    PASSWDDB = config["database"]["passwdpath"]
    LOGPATH = config["log"]["path"]

    # Creamos servidor de register y escuchamos
    s = SocketServer.UDPServer(("", int(sys.argv[1])), SIPRegisterHandler)
    print "Lanzando servidor UDP de SIP Register...\r\n\r\n"
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print "\r\nByeeee!!!!"
        sys.exit()
