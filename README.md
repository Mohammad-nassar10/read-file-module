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

We have `sample1.json` and `sample2.pdf` files to upload to s3 bucket using localstack.

### Register asset and secrets
```bash
kubectl apply -f sample/asset1.yaml -n fybrik-notebook-sample
kubectl apply -f sample/asset2.yaml -n fybrik-notebook-sample
```
Replace the values for access_key and secret_key in `sample_asset/secret-iceberg.yaml` file with the values from the object storage service that you used and run:
```bash
kubectl apply -f sample/secret1.yaml -n fybrik-notebook-sample
kubectl apply -f sample/secret2.yaml -n fybrik-notebook-sample
```

### Define data access policy
An example policy for allowing only `manager` role to access the files can be found in `sample/sample-policy.rego`. Run the following to deploy the policy.
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
