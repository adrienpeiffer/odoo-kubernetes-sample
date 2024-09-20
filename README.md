# odoo-kubernetes-sample

The objective of this repository is to present a simple dockerfile for the provisioning of an Odoo image based on the official one by adding additional addons and to present a simple structure of Kubernetes manifests.

## Components

In addition to the Odoo image, some additional components are required for the application to works properly. Persistent storage is required for this: 
- Odoo data - PostgreSQL
- Attachments
- User sessions

### PostgreSQL

For PostgreSQL data, we use CloudNativePG. It is the Kubernetes operator that covers the entire lifecycle of a highly available PostgreSQL database cluster with a primary/standby architecture using native streaming replication.

https://cloudnative-pg.io

### Attachments

For attachment, this example uses the OCA fs_attchement addon based on fsspec. This allows attachments to be sent to various storage devices, including s3 compatible storage and Azure file.

https://github.com/OCA/storage 

### User sessions

For session, this example uses the OCA session_db addon that give the possibility to store session directly on the database instead of local filesystem.


## Usage

### Prerequisite

In order to execute steps below, the following tools are required

- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [docker](https://docs.docker.com/engine/install/)
- [Kubernetes cluster with CloudNativePG](https://cloudnative-pg.io/documentation/1.24/quickstart/#installation)
- [K9S](https://k9scli.io/) (Optionnal)

### Image build

If you want to add additional addon on official Odoo image, you have to build the dockerfile

To build the Odoo image, we can use docker build command
`docker build -t kubernetes-sample .`

### Apply manifests on Kubernetes Cluster

In order to apply manifests from this repository, you have to setup a Kubernetes cluster with CloudNativePG operator installed.

Steps are well documented on [CloudNativePG documentation](https://cloudnative-pg.io/documentation/1.24/quickstart/#installation])

Once the cluster is ready, the manifests can be applied with `kubectl apply -k manifests`

Each manifest can be applied manually with `kubectl apply -f manifest/postgresql.yaml` for exemple
















