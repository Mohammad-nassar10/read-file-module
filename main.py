import argparse
from module.server import ReadServer



def init_ReadServer(args):
    ReadServer(args.config, args.port, args.loglevel.upper())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read Server')
    parser.add_argument(
        '-p', '--port', type=int, default=8484, help='Listening port for HTTP Server')
    parser.add_argument(
        '-c', '--config', type=str, default='/etc/conf/conf.yaml', help='Path to config file')
    parser.add_argument(
        '-l', '--loglevel', type=str, default='warning', help='logging level', 
        choices=['trace', 'info', 'debug', 'warning', 'error', 'critical'])
    # parser.add_argument(
        # '-w', '--workdir', type=str, default='/local', help='writable directory for temporary files')
    args = parser.parse_args()

    # start the HTTP server
    server = init_ReadServer(args)
