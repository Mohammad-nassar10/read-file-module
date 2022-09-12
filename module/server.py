import http.server
from http import HTTPStatus
import socketserver
import boto3
import base64
import json
import yaml
from fybrik_python_vault import get_jwt_from_file, get_raw_secret_from_vault
from fybrik_python_logging import logger
from .s3 import get_s3_credentials_from_vault


data_dict = {}


def get_details_from_conf(config_path):
    """ Parse the configuration and get the data details and policies """
    print("get details from conf")
    # with open("/etc/conf/conf.yaml", 'r') as stream:
    with open(config_path, 'r') as stream:
        content = yaml.safe_load(stream)
        for key, val in content.items():
            if "data" in key:
                for data in val:
                    dataset_id = data["name"]
                    name = dataset_id.split("/")[1]
                    endpoint_url = data["connection"]["s3"]["endpoint_url"]
                    bucket = data["connection"]["s3"]["bucket"]
                    object_key = data["connection"]["s3"]["object_key"]
                    vault_credentials = data["connection"]["s3"]["vault_credentials"]
                    creds = ['minio', 'minio123']
                    # creds = get_s3_credentials_from_vault(vault_credentials, dataset_id)
                    data_dict[name] = {'format': data["format"], 'endpoint_url': endpoint_url, 'bucket': bucket, 'object_key': object_key, 'path': data["path"], 'creds': creds}

    print(data_dict)
    return data_dict



def read_file(config_path, asset_name):
    # Set log level
    # init_logger("TRACE", "123", 'read-module')
    HTTP = 'http://'
    # HTTP = ''
    # Get the dataset details from configuration
    parse_conf_dict = get_details_from_conf(config_path)
    print(asset_name)
    if asset_name not in parse_conf_dict:
        return False
    parse_conf = parse_conf_dict[asset_name]
    print("conf dictionary")
    print(parse_conf)
    endpoint = parse_conf['endpoint_url']
    bucket_name = parse_conf['bucket']
    objet_key = parse_conf['object_key']
    path = parse_conf['path']
    creds = parse_conf['creds']
    aws_access_key_id = creds[0]
    aws_secret_access_key = creds[1]


    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=None,
        region_name="",
        botocore_session=None,
        profile_name=None)

    s3client = session.client(
    's3', endpoint_url=f"{HTTP}{endpoint}")
    s3resource = session.resource(
    's3', endpoint_url=f"{HTTP}{endpoint}")
    response = s3client.list_buckets()
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

    with open('/tmp/obj_file', 'wb') as f:
        s3client.download_fileobj(bucket_name, objet_key, f)
    
    return True




class HttpReadHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.config_path = server.config_path
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    '''
    do_GET() gets the asset name from the URL.
    for instance, if the URL is localhost:8080/userdata
    then the asset name is userdata.
    Obtain the dataset associated with the asset name, and
    return it to client.
    '''
    def do_GET(self):
       
        print("conf = " + self.config_path)
        asset_name = self.path.lstrip('/')
        print("get " + asset_name)
        read_success = read_file(self.config_path, asset_name)
        if read_success == False:
            logger.error('asset not found or malformed configuration')
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return
      
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write("response\n".encode())
        f = open('/tmp/obj_file', 'rb')
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            self.wfile.write(chunk)



class HttpReadServer(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass,
                 config_path):
        self.config_path = config_path
        socketserver.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)


class ReadServer():
    def __init__(self, config_path: str, port: int, loglevel: str):
        # with Config(config_path) as config:
        #     init_logger(loglevel, config.app_uuid, 'airbyte-module')

        server = HttpReadServer(("0.0.0.0", port), HttpReadHandler, config_path)
        server.serve_forever()