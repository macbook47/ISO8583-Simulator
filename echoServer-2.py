"""

this program copied and edited from :

(C) Copyright 2009 Igor V. Custodio

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


from ISO8583.ISO8583 import ISO8583
from ISO8583.ISOErrors import *
from socket import *
import struct
import signal
import sys
from termcolor import colored, cprint
from datetime import datetime
from datetime import timedelta

# Configure the server
serverIP = "10.23.179.205"
serverPort = 8583
maxConn = 5
bigEndian = True
# bigEndian = False


# Create a TCP socket
s = socket(AF_INET, SOCK_STREAM)
# bind it to the server port
s.bind((serverIP, serverPort))
# Configure it to accept up to N simultaneous Clients waiting...
s.listen(maxConn)


def signal_handler(signal, frame):
    print(colored('\nSystem killed', 'red'))
    s.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Run forever
while 1:
    # wait new Client Connection
    connection, address = s.accept()
    while 1:
        # receive message
        isoStr = connection.recv(2048)
        if isoStr:
            print (colored("\n" + datetime.now().strftime("%y-%m-%d %H:%m:%s") +
                           " - Input ASCII |%s|" % isoStr, 'green'))
            pack = ISO8583()
            check123 = isoStr[4:8]
            # parse the iso
            try:
                if isoStr[4:8] == '0800':
                    bigEndian = False
                    isoStrWithHead = struct.pack(
                        '<h', len(isoStr[4:])) + isoStr[4:]

                else:
                    bigEndian = True
                    isoStrWithHead = struct.pack(
                        '!h', len(isoStr[4:])) + isoStr[4:]

                if bigEndian:
                    pack.setNetworkISO(isoStrWithHead)
                else:
                    pack.setNetworkISO(isoStrWithHead, False)

                v1 = pack.getBitsAndValues()
                for v in v1:
                    print (colored('Bit %s of type %s with value = %s' %
                                   (v['bit'], v['type'], v['value']), 'blue'))

                if pack.getMTI() == '0200' and pack.getBit(3) == '370000':
                    print (colored("\n" + datetime.now().strftime("%y-%m-%d %H:%m:%s") +
                                   " - Got Inquiry Request", 'yellow'))
                    # send answer
                    pack.setMTI('0210')
                    pack.setBit(2, '6013010900000416')
                    pack.setBit(4, '000001725000')
                    if int(pack.getBit(12)) > 150000:
                        pack.setBit(15, (datetime.now() +
                                         timedelta(days=1)).strftime("%m%d"))
                    else:
                        pack.setBit(
                            15, datetime.now().strftime("%m%d"))
                    pack.setBit(39, '00')
                    add61 = "0271670AE 3174061205830005"
                    add62 = "1670AE 03SEDAN        HYUNDAI   EXEL X 3 MT         200601495001066000000021400000000000000000000000000014300000003500000500000000000001                                                            07102017X10             00002006             3174061205830005"
                    pack.setBit(61, add61)
                    pack.setBit(62, add62)
                    pack.setBit(98, '010011')
                    pack.setBit(102, '301001001071509')
                    bigEndian = True

                elif pack.getMTI() == '0200' and pack.getBit(3) == '500000':
                    print (colored("\n" + datetime.now().strftime("%y-%m-%d %H:%m:%s") +
                                   " - Got Payment Request", 'yellow'))
                    # send answer
                    pack.setMTI('0210')
                    pack.setBit(2, '6013010900000416')
                    pack.setBit(4, '000001315400')
                    pack.setBit(39, '00')
                    add61 = "1670AE 317406120583000507102018001066000001066000000000000000000000000000014300000003500000500000000000"
                    add62 = "1670AE 03SEDAN        HYUNDAI   EXEL X 3 MT         200601495001066000001066000000000000000000000000000014300000003500000500000000000001GIDEON PURWANANDA T      CILANDAK TENGAH III/45 RT 1/1 JS   07102018X10BENSIN       20062006             3174061205830005171016Z10000001 "
                    pack.setBit(61, add61)
                    pack.setBit(62, add62)
                    pack.setBit(98, '010011')
                    pack.setBit(102, '301001001071509')
                    bigEndian = True

                elif pack.getMTI() == '0800':
                    print (colored("\n" + datetime.now().strftime("%y-%m-%d %H:%m:%s") +
                                   " - Got Network Request", 'yellow'))
                    # send answer
                    pack.setMTI('0810')
                    pack.setBit(39, '00')
                    bigEndian = False

                else:
                    print ("\n" + datetime.now().strftime("%y-%m-%d %H:%m:%s") +
                           " - The client dosen't send the correct message!")
                    break

            except InvalidIso8583, ii:
                print ii
                break
            except:
                print ('Something happened!!!!')
                break

            if bigEndian:
                ans = pack.getNetworkISO()
            else:
                ans = pack.getNetworkISO(False)

            anspacked = str(len(ans[2:])).zfill(4) + ans[2:]
            print (colored("\n" + datetime.now().strftime("%y-%m-%d %H:%m:%s") +
                           " - Sending answer |%s|" % anspacked, 'yellow'))
            print ('\n')
            connection.send(anspacked)

        else:
            break
    # close socket
    connection.close()
    print (colored("Closed...", 'red'))
