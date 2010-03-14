# -*- coding: utf-8 -*-
#
# Name: Pyton Twisted binary file transfer demo (client)
# Description: Simple demo which shows how you can transfer binary files using
# the Twisted framework.
#
# Keep in mind that this is only a demo and there are many possible scenarios
# where program can break.
#
# Author: Tomaž Muraus (http://www.tomaz-muraus.info)
# License: GPL

# Requirements:
# - Python >= 2.5
# - Twisted (http://twistedmatrix.com/)

import os
import optparse

from twisted.internet import reactor, protocol, stdio, defer
from twisted.protocols import basic
from twisted.internet.protocol import ClientFactory

from common import COMMANDS, display_message, validate_file_md5_hash, get_file_md5_hash, read_bytes_from_file, clean_and_split_input

class CommandLineProtocol(basic.LineReceiver):
    delimiter = '\n'
    
    def __init__(self, server_ip, server_port, files_path):
        self.server_ip = server_ip
        self.server_port = server_port
        self.files_path = files_path
    
    def connectionMade(self):  
        self.factory = FileTransferClientFactory(self.files_path)
        self.connection = reactor.connectTCP(self.server_ip, self.server_port, self.factory)
        self.factory.deferred.addCallback(self._display_response)
        
    def lineReceived(self, line):
        """ If a line is received, call sendCommand(), else prompt user for input. """
        
        if not line:
            self._prompt()
            return
        
        self._sendCommand(line)
        
    def _sendCommand(self, line):
        """ Sends a command to the server. """
        
        data = clean_and_split_input(line) 
        if len(data) == 0 or data == '':
            return 

        command = data[0].lower()
        if not command in COMMANDS:
            self._display_message('Invalid command')
            return
        
        if command == 'list' or command == 'help' or command == 'quit':
            self.connection.transport.write('%s\n' % (command))
        elif command == 'get':
            try:
                filename = data[1]
            except IndexError:
                self._display_message('Missing filename')
                return
            
            self.connection.transport.write('%s %s\n' % (command, filename))
        elif command == 'put':
            try:
                file_path = data[1]
                filename = data[2]
            except IndexError:
                self._display_message('Missing local file path or remote file name')
                return
            
            if not os.path.isfile(file_path):
                self._display_message('This file does not exist')
                return

            file_size = os.path.getsize(file_path) / 1024
            
            print 'Uploading file: %s (%d KB)' % (filename, file_size)
            
            self.connection.transport.write('PUT %s %s\n' % (filename, get_file_md5_hash(file_path)))
            self.setRawMode()
            
            for bytes in read_bytes_from_file(file_path):
                self.connection.transport.write(bytes)
            
            self.connection.transport.write('\r\n')   
            
            # When the transfer is finished, we go back to the line mode 
            self.setLineMode()
        else:
            self.connection.transport.write('%s %s\n' % (command, data[1]))

        self.factory.deferred.addCallback(self._display_response)
        
    def _display_response(self, lines = None):
        """ Displays a server response. """
        
        if lines:
            for line in lines:
                print '%s' % (line)
            
        self._prompt()
        self.factory.deferred = defer.Deferred()
        
    def _prompt(self):
        """ Prompts user for input. """
        self.transport.write('> ')
        
    def _display_message(self, message):
        """ Helper function which prints a message and prompts user for input. """
        
        print message
        self._prompt()    

class FileTransferProtocol(basic.LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        self.buffer = []
        self.file_handler = None
        self.file_data = ()
        
        print 'Connected to the server'
        
    def connectionLost(self, reason):
        self.file_handler = None
        self.file_data = ()
        
        print 'Connection to the server has been lost'
        reactor.stop()
    
    def lineReceived(self, line):
        if line == 'ENDMSG':
            self.factory.deferred.callback(self.buffer)
            self.buffer = []
        elif line.startswith('HASH'):
            # Received a file name and hash, server is sending us a file
            data = clean_and_split_input(line)

            filename = data[1]
            file_hash = data[2]
            
            self.file_data = (filename, file_hash)
            self.setRawMode()
        else:
            self.buffer.append(line)
        
    def rawDataReceived(self, data):
        filename = self.file_data[0]
        file_path = os.path.join(self.factory.files_path, filename)
        
        print 'Receiving file chunk (%d KB)' % (len(data))
        
        if not self.file_handler:
            self.file_handler = open(file_path, 'wb')
            
        if data.endswith('\r\n'):
            # Last chunk
            data = data[:-2]
            self.file_handler.write(data)
            self.setLineMode()
            
            self.file_handler.close()
            self.file_handler = None
            
            if validate_file_md5_hash(file_path, self.file_data[1]):
                print 'File %s has been successfully transfered and saved' % (filename)
            else:
                os.unlink(file_path)
                print 'File %s has been successfully transfered, but deleted due to invalid MD5 hash' % (filename)
        else:
            self.file_handler.write(data)

class FileTransferClientFactory(protocol.ClientFactory):
    protocol = FileTransferProtocol
    
    def __init__(self, files_path):
        self.files_path = files_path
        self.deferred = defer.Deferred()

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--ip', action = 'store', type = 'string', dest = 'ip_address', default = '127.0.0.1', help = 'server IP address')
    parser.add_option('-p', '--port', action = 'store', type = 'int', dest = 'port', default = 1234, help = 'server port')
    parser.add_option('--path', action = 'store', type = 'string', dest = 'path', help = 'directory where the incoming files are saved')
    
    (options, args) = parser.parse_args()

    print 'Client started, incoming files will be saved to %s' % (options.path)
    
    stdio.StandardIO(CommandLineProtocol(options.ip_address, options.port, options.path))
    reactor.run()    