#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import SocketServer
import sys
import os


class SIPHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """
    def mensaje(self, code):
        """
        Devuelve un string con la forma del mensaje a enviar
        Halla el método a partir del código
        """
        if code == "100":
            metodo = "Trying"
        elif code == "180":
            metodo = "Ringing"
        elif code == "200":
            metodo = "OK"
        elif code == "400":
            metodo = "Bad Request"
        elif code == "405":
            metodo = "Method not allowed"

        msg = "SIP/2.0 " + code + " " + metodo + "\r\n\r\n"
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
        line = self.rfile.read()
        print "El cliente nos manda ==> " + line
        metodo = line.split()[0]
        prot = line.split()[2]
        if metodo == "INVITE":
            self.send("100")  # Send interpreta el Trying y añade Ringing y OK
        elif metodo == "ACK":
            comando = "./mp32rtp -i 127.0.0.1 -p 23032 < " + FILE
            print "Enviando archivo...\r\n\r\n"
            os.system(comando)
        elif metodo == "BYE":
            self.send("200")
        elif prot != "SIP/2.0":
            self.send("400")
        else:
            self.send("405")

if __name__ == "__main__":

    USAGE = "Usage: python server.py IP port audio_file"

    # Creamos servidor de eco y escuchamos
    if len(sys.argv) == 4:
        IP = sys.argv[1]
        PORT = int(sys.argv[2])
        FILE = sys.argv[3]
        s = SocketServer.UDPServer((IP, PORT), SIPHandler)
        print "Listening...\r\n"
        s.serve_forever()
    else:
        print USAGE
