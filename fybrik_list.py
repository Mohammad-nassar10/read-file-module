import argparse
import os
from time import sleep
import yaml
from pathlib import Path


def main(role, bucket):
    fybrikAppDict = {'apiVersion': 'app.fybrik.io/v1alpha1', 
                        'kind': 'FybrikApplication', 
                        'metadata': {'name': 'my-notebook', 'labels': {'app': 'my-notebook'}}, 
                        'spec': {
                            'selector': {'workloadSelector': {'matchLabels': {'app': 'my-notebook'}}}, 
                            'appInfo': {'intent': 'Fraud Detection', 'role': role}, 
                            'data': []}}

    allowed = []
    denied = []
    stream = os.popen('kubectl get asset -A')
    output = stream.readlines()
    assets = [r.split()[0]+'/'+ r.split()[1] for r in output[1:]]
    for asset in assets:
        os.system('kubectl get asset ' + asset.split('/')[1] + ' -n ' + asset.split('/')[0]  + ' -o yaml > tmpAsset.yaml')
        yaml_dict = yaml.safe_load(Path("tmpAsset.yaml").read_text())
        bucket_name = yaml_dict['spec']['details']['connection']['s3']['bucket']
        if bucket_name == bucket:
            fybrikAppDict['spec']['data'].append({'dataSetID': asset, 'requirements': {'interface': {'protocol': 'http'}}})
        os.system('rm tmpAsset.yaml')
    
    # print(fybrikAppDict)
    with open('fybrikappGen.yaml', 'w') as outfile:
        yaml.dump(fybrikAppDict, outfile, default_flow_style=False)
    
    os.system('kubectl apply -f fybrikappGen.yaml')
    sleep(30)
    os.system('kubectl get fybrikapplication my-notebook -o yaml > app_status.yaml')

    yaml_dict = yaml.safe_load(Path("app_status.yaml").read_text())
    for asset in assets:
        status = yaml_dict['status']['assetStates'][asset]['conditions'][0]['status']
        # print(status)
        if status == 'True':
            endpoint = yaml_dict['status']['assetStates'][asset]['endpoint']
            allowed.append({'asset': asset, 'endpoint': endpoint})
        else:
            denied.append(asset)
    os.system('rm app_status.yaml')
    print(allowed, denied)
    return allowed, denied

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ABM Server')
    parser.add_argument(
        '-r', '--role', type=str, default="Developer", help='Role')
    parser.add_argument(
        '-b', '--bucket', type=str, default="demo", help='Bucket name')
    args = parser.parse_args()

    main(args.role, args.bucket)