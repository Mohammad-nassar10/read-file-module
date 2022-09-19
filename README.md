[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# read-file-module

### Install Fybrik
Fybrik [Quick Start (v1.1)](https://fybrik.io/v1.1/get-started/quickstart/), without the section of `Install modules`.

### Create namespace
```bash
kubectl create namespace fybrik-notebook-sample
kubectl config set-context --current --namespace=fybrik-notebook-sample
```

### Prepare datasets
Follow the section [`setup and upload to localstack`](https://fybrik.io/v0.6/samples/notebook/#prepare-a-dataset-to-be-accessed-by-the-notebook) in order to upload files to an object storage.

For example:

We have `sample1.json` and `sample2.pdf` files to upload to an s3 bucket using localstack.

- <details><summary>Upload sample1.json and sample2.pdf</summary>

     1. Define variables for access key and secret key:
        ```bash
        export ACCESS_KEY="myaccesskey"
        export SECRET_KEY="mysecretkey"
        ```
     1. Install localstack to the currently active namespace and wait for it to be ready:
        ```bash
        helm repo add localstack-charts https://localstack.github.io/helm-charts
        helm install localstack localstack-charts/localstack --set startServices="s3" --set service.type=ClusterIP
        kubectl wait --for=condition=ready --all pod -n fybrik-notebook-sample --timeout=120s
        ```
    1. Create a port-forward to communicate with localstack server:
        ```bash
        kubectl port-forward svc/localstack 4566:4566 &
        ```
    1. Use AWS CLI to upload the files to a new created bucket in the localstack server:
        ```bash
        export ENDPOINT="http://127.0.0.1:4566"
        export BUCKET="demo"
        export OBJECT_KEY="sample1.json"
        export FILEPATH="/path/to/sample1.json"
        aws configure set aws_access_key_id ${ACCESS_KEY} && aws configure set aws_secret_access_key ${SECRET_KEY} && aws --endpoint-url=${ENDPOINT} s3api create-bucket --bucket ${BUCKET} --region us-east-1 && aws --endpoint-url=${ENDPOINT} s3api put-object --bucket ${BUCKET} --key ${OBJECT_KEY} --body ${FILEPATH}
        export OBJECT_KEY="sample2.pdf"
        export FILEPATH="/path/to/sample2.pdf"
        aws --endpoint-url=${ENDPOINT} s3api put-object --bucket ${BUCKET} --key ${OBJECT_KEY} --body ${FILEPATH}
        ```

</details>

### Register assets
An `asset.yaml` file describes an asset by specifying the connection details, metadata, tags, and more.
```bash
kubectl apply -f sample/asset1.yaml -n fybrik-notebook-sample
kubectl apply -f sample/asset2.yaml -n fybrik-notebook-sample
```
For example, we have two assets, one for the file `sample1.json` which has been marked with `finance` tag. The second one for the file `sample2.pdf` which has been marked as not `finance`.

### Register secrets
Replace the values for access_key and secret_key in `sample/secret1.yaml` and `sample/secret2.yaml` files with the values from the object storage service that you used and run:
```bash
kubectl apply -f sample/secret1.yaml -n fybrik-notebook-sample
kubectl apply -f sample/secret2.yaml -n fybrik-notebook-sample
```

### Define data access policy
Register a data policy. The example policy found in `sample/sample-policy.rego` allows `managers` to read assets tagged with `finance`. Run the following to deploy the policy.
```bash
kubectl -n fybrik-system create configmap sample-policy --from-file=sample/sample-policy.rego
kubectl -n fybrik-system label configmap sample-policy openpolicyagent.org/policy=rego
while [[ $(kubectl get cm sample-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' ]]; do echo "waiting for policy to be applied" && sleep 5; done
```

### Register the fybrikmodule:

```bash
kubectl apply -f module.yaml -n fybrik-system
```

### Deploy Fybrik application which triggers the module
```bash
kubectl apply -f sample/fybrikapplication.yaml
```
This sample `fybrikapplication` has a `manager` role and asks for the two assets `asset1` and `asset2`.
Run the following command to wait until the fybrikapplication be ready.
```bash
while [[ $(kubectl get fybrikapplication my-notebook -o 'jsonpath={.status.ready}') != "true" ]]; do echo "waiting for FybrikApplication" && sleep 5; done
```

A pod that runs an http server should be running in `fybrik-blueprints` namespace. You can run `port-forward` command to use the server from the host.
```bash
kubectl port-forward svc/my-notebook-fybrik-notebook-sample-read -n fybrik-blueprints 8484:80 &
```
Then, you can get <asset_name> asset by running the following command.
```bash
curl localhost:8484/<asset_name>
```
For example, you should get the content of the file `sample1.json` if you run the following command:
```bash
curl localhost:8484/asset1
```
But, due to the data policy that denies reading assets without `finance` tag, you will not get the content of the file `sample2.pdf` if you run the following command:
```bash
curl localhost:8484/asset2
```

### Cleanup
When you’re finished experimenting with the module, clean it up:
1. Stop kubectl port-forward processes (e.g., using pkill kubectl).
1. Delete the fybrik-notebook-sample namespace:
    ```bash
    kubectl delete namespace fybrik-notebook-sample
    ```
1. Delete the policy created in the fybrik-system namespace:
    ```bash
    NS="fybrik-system"; kubectl -n $NS get configmap | awk '/sample/{print $1}' | xargs  kubectl delete -n $NS configmap
    ```