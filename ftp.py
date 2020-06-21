"""
 Small ftp server for ESP8266 and ESP32 Micropython

 Based on the work of chrisgp - Christopher Popp and pfalcon - Paul Sokolovsky

 The server accepts passive mode only.
 It runs in a separated thread

 Start the server with:
   from ftp import ftpserver
   u = ftpserver()
   u.start_thread()

 Distributed under MIT License
 Copyright (c) 2016 Christopher Popp (initial ftp server framework)
 Copyright (c) 2016 Robert Hammelrath (putting the pieces together and a few extensions)
 Copyright (c) 2017 Mauro Riva (lemariva.com) (ftp class, dbg option and threading (only ESP32))
 Copyright (c) 2018 Gautier HUSSON (liberasys.com) (reentrancy)
"""

import socket
import network
import uos
from utime import localtime
import gc

try:
    import _thread
    thread_available = True
except:
    thread_available = False


DEBUG = False
#DEBUG = True

def dbg(msg, msg_=""):
    global DEBUG
    if DEBUG:
        print (str(msg) + str(msg_))


class ftpserver():
    def send_list_data(self, path, dataclient, full):
        try:
            # whether path is a directory name
            for fname in sorted(uos.listdir(path), key = str.lower):
                dataclient.sendall(self.make_description(path, fname, full))
        except:
            # path may be a file name or pattern
            pattern = path.split("/")[-1]
            path = path[:-(len(pattern) + 1)]
            if path == "": path = "/"
            for fname in sorted(uos.listdir(path), key = str.lower):
                if fncmp(fname, pattern):
                    dataclient.sendall(self.make_description(path, fname, full))

    def make_description(self, path, fname, full):
        if full:
            stat = uos.stat(self.get_absolute_path(path,fname))
            file_permissions = "drwxr-xr-x" if (stat[0] & 0o170000 == 0o040000) else "-rw-r--r--"
            file_size = stat[6]
            description = "{}    1 owner group {:>10} Jan 1 2000 {}\r\n".format(file_permissions, file_size, fname)
        else:
            description = fname + "\r\n"
        return description

    def send_file_data(self, path, dataclient):
        with open(path, "r") as file:
            chunk = file.read(512)
            while len(chunk) > 0:
                dataclient.sendall(chunk)
                chunk = file.read(512)

    def save_file_data(self, path, dataclient):
        with open(path, "w") as file:
            chunk = dataclient.recv(512)
            while len(chunk) > 0:
                file.write(chunk)
                chunk = dataclient.recv(512)

    def get_absolute_path(self, cwd, payload):
        # Just a few special cases "..", "." and ""
        # If payload start's with /, set cwd to /
        # and consider the remainder a relative path
        if payload.startswith('/'):
            cwd = "/"
        for token in payload.split("/"):
            if token == '..':
                if cwd != '/':
                    cwd = '/'.join(cwd.split('/')[:-1])
                    if cwd == '':
                        cwd = '/'
            elif token != '.' and token != '':
                if cwd == '/':
                    cwd += token
                else:
                    cwd = cwd + '/' + token
        return cwd

    # compare fname against pattern. Pattern may contain
    # wildcards ? and *.
    def fncmp(fname, pattern):
        pi = 0
        si = 0
        while pi < len(pattern) and si < len(fname):
            if (fname[si] == pattern[pi]) or (pattern[pi] == '?'):
                si += 1
                pi += 1
            else:
                if pattern[pi] == '*': # recurse
                    if (pi + 1) == len(pattern):
                        return True
                    while si < len(fname):
                        if fncmp(fname[si:], pattern[pi+1:]):
                            return True
                        else:
                            si += 1
                    return False
                else:
                    return False
        if pi == len(pattern.rstrip("*")) and si == len(fname):
            return True
        else:
            return False

    def thread_ftp(self, arg):
        self.start()
        dbg('Thread ftp ended')

    def start_thread(self):
        if thread_available:
            dbg("Starting ftp server on separated thread\n")
            _thread.start_new_thread(self.thread_ftp, ('',))
        else:
            self.start()

    def start(self):
        DATA_PORT = 13333

        self.ftpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.ftpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.datasocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.ftpsocket.bind(socket.getaddrinfo("0.0.0.0", 21)[0][4])
        self.datasocket.bind(socket.getaddrinfo("0.0.0.0", DATA_PORT)[0][4])

        self.ftpsocket.listen(1)
        self.ftpsocket.settimeout(None)
        self.datasocket.listen(1)
        self.datasocket.settimeout(None)

        msg_250_OK = '250 OK\r\n'
        msg_550_fail = '550 Failed\r\n'
        self.wlan = network.WLAN(network.AP_IF)
        if self.wlan.active():
            ifconfig = self.wlan.ifconfig()
        else:
            self.wlan = network.WLAN(network.STA_IF)
            if self.wlan.active():
                ifconfig = self.wlan.ifconfig()
            else:
                dbg("No active connection")
                return
        addr = ifconfig[0]
        print("FTP Server started on ", addr)

        try:
            while True:
                dataclient = None
                fromname = None
                do_run = True
                while do_run:
                    cl, remote_addr = self.ftpsocket.accept()
                    cl.settimeout(300)
                    cwd = '/'
                    try:
                        dbg("FTP connection from:", remote_addr)
                        cl.sendall("220 Hello, this is the " + uos.uname()[4] + ".\r\n")
                        while True:
                            data = cl.readline().decode("utf-8").rstrip("\r\n")
                            if len(data) <= 0:
                                dbg("Client disappeared")
                                do_run = False
                                break

                            command = data.split(" ")[0].upper()
                            payload = data[len(command):].lstrip()

                            path = self.get_absolute_path(cwd, payload)

                            dbg("Command={}, Payload={}".format(command, payload))

                            if command == "USER":
                                cl.sendall("230 Logged in.\r\n")
                            elif command == "SYST":
                                cl.sendall("215 UNIX Type: L8\r\n")
                            elif command == "NOOP":
                                cl.sendall("200 OK\r\n")
                            elif command == "FEAT":
                                cl.sendall("211 no-features\r\n")
                            elif command == "PWD" or command == "XPWD":
                                cl.sendall('257 "{}"\r\n'.format(cwd))
                            elif command == "CWD":
                                try:
                                    files = uos.listdir(path)
                                    cwd = path
                                    cl.sendall(msg_250_OK)
                                except:
                                    cl.sendall(msg_550_fail)
                            elif command == "CDUP":
                                cwd = self.get_absolute_path(cwd, "..")
                                cl.sendall(msg_250_OK)
                            elif command == "TYPE":
                                # probably should switch between binary and not
                                cl.sendall('200 Transfer mode set\r\n')
                            elif command == "SIZE":
                                try:
                                    size = uos.stat(path)[6]
                                    cl.sendall('213 {}\r\n'.format(size))
                                except:
                                    cl.sendall(msg_550_fail)
                            elif command == "QUIT":
                                cl.sendall('221 Bye.\r\n')
                                do_run = False
                                break
                            elif command == "PASV":
                                cl.sendall('227 Entering Passive Mode ({},{},{}).\r\n'.format(
                                    addr.replace('.',','), DATA_PORT>>8, DATA_PORT%256))
                                dataclient, data_addr = self.datasocket.accept()
                                dbg("FTP Data connection from:", data_addr)
                            elif command == "LIST" or command == "NLST":
                                if not payload.startswith("-"):
                                    place = path
                                else:
                                    place = cwd
                                try:
                                    self.send_list_data(place, dataclient, command == "LIST" or payload == "-l")
                                    cl.sendall("150 Here comes the directory listing.\r\n")
                                    cl.sendall("226 Listed.\r\n")
                                except:
                                    cl.sendall(msg_550_fail)
                                if dataclient is not None:
                                    dataclient.close()
                                    dataclient = None
                            elif command == "RETR":
                                try:
                                    self.send_file_data(path, dataclient)
                                    cl.sendall("150 Opening data connection.\r\n")
                                    cl.sendall("226 Transfer complete.\r\n")
                                except:
                                    cl.sendall(msg_550_fail)
                                if dataclient is not None:
                                    dataclient.close()
                                    dataclient = None
                            elif command == "STOR":
                                try:
                                    cl.sendall("150 Ok to send data.\r\n")
                                    self.save_file_data(path, dataclient)
                                    cl.sendall("226 Transfer complete.\r\n")
                                except:
                                    cl.sendall(msg_550_fail)
                                if dataclient is not None:
                                    dataclient.close()
                                    dataclient = None
                            elif command == "DELE":
                                try:
                                    uos.remove(path)
                                    cl.sendall(msg_250_OK)
                                except:
                                    cl.sendall(msg_550_fail)
                            elif command == "RMD" or command == "XRMD":
                                try:
                                    uos.rmdir(path)
                                    cl.sendall(msg_250_OK)
                                except:
                                    cl.sendall(msg_550_fail)
                            elif command == "MKD" or command == "XMKD":
                                try:
                                    uos.mkdir(path)
                                    cl.sendall(msg_250_OK)
                                except:
                                    cl.sendall(msg_550_fail)
                            elif command == "RNFR":
                                    fromname = path
                                    cl.sendall("350 Rename from\r\n")
                            elif command == "RNTO":
                                    if fromname is not None:
                                        try:
                                            uos.rename(fromname, path)
                                            cl.sendall(msg_250_OK)
                                        except:
                                            cl.sendall(msg_550_fail)
                                    else:
                                        cl.sendall(msg_550_fail)
                                    fromname = None
                            elif command == "MDTM":
                                try:
                                    tm=localtime(uos.stat(path)[8])
                                    cl.sendall('213 {:04d}{:02d}{:02d}{:02d}{:02d}{:02d}\r\n'.format(*tm[0:6]))
                                except:
                                    cl.sendall('550 Fail\r\n')
                            elif command == "STAT":
                                if payload == "":
                                    cl.sendall("211-Connected to ({})\r\n"
                                               "    Data address ({})\r\n"
                                               "211 TYPE: Binary STRU: File MODE: Stream\r\n".format(
                                               remote_addr[0], addr))
                                else:
                                    cl.sendall("213-Directory listing:\r\n")
                                    self.send_list_data(path, cl, True)
                                    cl.sendall("213 Done.\r\n")
                            else:
                                cl.sendall("502 Unsupported command.\r\n")
                                dbg("Unsupported command {} with payload {}".format(command, payload))
                    except Exception as err:
                        dbg(err)
                    finally:
                        cl.close()
                        cl = None
                        if dataclient is not None:
                            dataclient.close()

        finally:
            self.datasocket.close()
            self.ftpsocket.close()
