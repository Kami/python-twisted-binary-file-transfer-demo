import hashlib
from datetime import datetime

COMMANDS = {
            'list': ('list', 'Displays a list of all the available files'),
            'get': ('get <remote filename>', 'Downloads a file with a given filename'),
            'put': ('put <local file path> <remote file name>', 'Uploads a file with a given filename'),
            'help': ('help', 'Displays a list of all the available commands'),
            'quit': ('quit', 'Disconnects from the server'),
}

def timestamp():
    """ Returns current time stamp. """
    return '[%s]'  % (datetime.strftime(datetime.now(), '%H:%M:%S'))

def display_message(message):
    """ Displays a message with a prepended time stamp. """
    
    print '%s %s' % (timestamp(), message)

def validate_file_md5_hash(file, original_hash):
    """ Returns true if file MD5 hash matches with the provided one, false otherwise. """

    if get_file_md5_hash(file) == original_hash:
        return True
        
    return False

def get_file_md5_hash(file):
    """ Returns file MD5 hash"""
    
    md5_hash = hashlib.md5()
    for bytes in read_bytes_from_file(file):
        md5_hash.update(bytes)
        
    return md5_hash.hexdigest()

def read_bytes_from_file(file, chunk_size = 8100):
    """ Read bytes from a file in chunks. """
    
    with open(file, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            
            if chunk:
                    yield chunk
            else:
                break

def clean_and_split_input(input):
    """ Removes carriage return and line feed characters and splits input on a single whitespace. """
    
    input = input.strip()
    input = input.split(' ')
        
    return input