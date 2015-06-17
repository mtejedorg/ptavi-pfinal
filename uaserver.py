#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import SocketServer
import sys
import os
import time
import uaclient
#from uaclient import ConfigXMLHandler
#from uaclient import log
#from uaclient import get_fecha
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    def mensaje(self, code):
        """
        Devuelve un string con la forma del mensaje a enviar
        Halla el método a partir del código
        """
        sdphead = "\r\n"
        if code == "100":
            metodo = "Trying"
        elif code == "180":
            metodo = "Ringing"
        elif code == "200":
            metodo = "OK"
            sdphead += "Content-Type: application/sdp\r\n\r\n"
            sdphead += "v=o\r\n"                               # v
            sdphead += "o=" + NAME + " " + IP + "\r\n"         # o
            sdphead += "s=sesionchachi\r\n"                    # s
            sdphead += "t=0\r\n"                               # t
            sdphead += "m=audio " + str(RTP_PORT) + " RTP\r\n"     # m
        elif code == "400":
            metodo = "Bad Request"
        elif code == "405":
            metodo = "Method not allowed"

        msg = "SIP/2.0 " + code + " " + metodo + sdphead + "\r\n"
        return msg

    def send(self, code):
        """ Envía al servidor un mensaje usando el código como parámetro """
        if code == "100":
            msg = self.mensaje("100")
            msg += self.mensaje("180")
            msg += self.mensaje("200")
        else:
            msg = self.mensaje(code)
        print "Enviando: " + msg
        self.wfile.write(msg)

    def handle(self):
        """ Recibe los mensajes y se encarga de responder """
        data = self.rfile.read()
        lines = data.split("\r\n")
        print "El cliente nos manda ==> " + data
        metodo = data.split()[0]
        prot = data.split()[2]
        if metodo == "Invite":
            self.send("100")  # Send interpreta el Trying y añade Ringing y OK
            # Almacenamos los datos de envío RTP
            for line in lines:
                if line.split("=")[0] == "o":
                    rtpclient["IP"] = line.split(" ")[1]
                if line.split("=")[0] == "m":
                    rtpclient["port"] = line.split(" ")[1]
        elif metodo == "Ack":
            # Enviamos el audio por RTP
            comando = "./mp32rtp -i " + rtpclient["IP"]
            comando += " -p " + str(rtpclient["port"])
            comando += " < " + FILE
            print "Enviando archivo...\r\n\r\n"
            os.system(comando)
            print "Archivo enviado"
        elif metodo == "Bye":
            self.send("200")
        elif prot != "SIP/2.0":
            self.send("400")
        else:
            self.send("405")

if __name__ == "__main__":

    USAGE = "Usage: python uaserver.py config"
    # Implementado para un único cliente simultáneo
    rtpclient = {}

    # Creamos servidor de eco y escuchamos
    if len(sys.argv) != 2:
        print USAGE
        sys.exit()

    # Creamos un objeto de la clase ConfigXMLHandler
    CONFIGFILE = sys.argv[1]
    xmlHandler = uaclient.ConfigXMLHandler()
    parser = make_parser()
    parser.setContentHandler(xmlHandler)
    parser.parse(open(CONFIGFILE))
    config = xmlHandler.get_config()

    # Extraemos la información de nuestro diccionario
    if config["uaserver"]["ip"] != "":
        IP = config["uaserver"]["ip"]
    else:
        IP = "127.0.0.1"
    PORT = int(config["uaserver"]["puerto"])
    NAME = config["account"]["username"]

    FILE = config["audio"]["path"]
    LOGPATH = config["log"]["path"]

    RTP_PORT = int(config["rtpaudio"]["puerto"])

    s = SocketServer.UDPServer((IP, PORT), SIPHandler)

    fich = open(LOGPATH, "a")  # Abrimos el archivo de log
    uaclient.log("Starting...\r\n", fich)
    print "Listening...\r\n"
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print "\r\nByeeee!!!!"
        sys.exit()
