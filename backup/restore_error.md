
rvices/https:metrics-server:https/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

Do you want to continue? (yes/no): yes
Creating namespaces...
namespace/cloudforet created
namespace/cloudforet-plugin created
Restoring ConfigMaps and Secrets...
configmap/board-application-grpc-conf created
configmap/board-application-rest-conf created
configmap/board-application-scheduler-conf created
configmap/board-application-worker-conf created
configmap/board-conf created
configmap/board-database-conf created
configmap/cfctl-environment-conf created
configmap/config-application-grpc-conf created
configmap/config-application-rest-conf created
configmap/config-application-scheduler-conf created
configmap/config-application-worker-conf created
configmap/config-conf created
configmap/config-database-conf created
configmap/console-api-conf created
configmap/console-api-nginx-conf created
configmap/console-api-nginx-proxy-conf created
configmap/console-api-v2-application-grpc-conf created
configmap/console-api-v2-application-rest-conf created
configmap/console-api-v2-application-scheduler-conf created
configmap/console-api-v2-application-worker-conf created
configmap/console-api-v2-conf created
configmap/console-api-v2-database-conf created
configmap/console-api-v2-rest-nginx-conf created
configmap/console-api-v2-rest-nginx-proxy-conf created
configmap/console-conf created
configmap/console-nginx-conf created
configmap/cost-analysis-application-grpc-conf created
configmap/cost-analysis-application-rest-conf created
configmap/cost-analysis-application-scheduler-conf created
configmap/cost-analysis-application-worker-conf created
configmap/cost-analysis-conf created
configmap/cost-analysis-database-conf created
configmap/dashboard-application-grpc-conf created
configmap/dashboard-application-rest-conf created
configmap/dashboard-application-scheduler-conf created
configmap/dashboard-application-worker-conf created
configmap/dashboard-conf created
configmap/dashboard-database-conf created
configmap/file-manager-application-grpc-conf created
configmap/file-manager-application-rest-conf created
configmap/file-manager-application-scheduler-conf created
configmap/file-manager-application-worker-conf created
configmap/file-manager-conf created
configmap/file-manager-database-conf created
configmap/file-manager-rest-nginx-conf created
configmap/file-manager-rest-nginx-proxy-conf created
configmap/identity-application-grpc-conf created
configmap/identity-application-rest-conf created
configmap/identity-application-scheduler-conf created
configmap/identity-application-worker-conf created
configmap/identity-conf created
configmap/identity-database-conf created
configmap/inventory-application-grpc-conf created
configmap/inventory-application-rest-conf created
configmap/inventory-application-scheduler-conf created
configmap/inventory-application-worker-conf created
configmap/inventory-conf created
configmap/inventory-database-conf created
Warning: resource configmaps/kube-root-ca.crt is missing the kubectl.kubernetes.io/last-applied-configuration annotation which is required by kubectl apply. kubectl apply should only be used on resources created declaratively by either kubectl create --save-config or kubectl apply. The missing annotation will be patched automatically.
configmap/mongodb-user-conf created
configmap/monitoring-application-grpc-conf created
configmap/monitoring-application-rest-conf created
configmap/monitoring-application-scheduler-conf created
configmap/monitoring-application-worker-conf created
configmap/monitoring-conf created
configmap/monitoring-database-conf created
configmap/monitoring-rest-nginx-conf created
configmap/monitoring-rest-nginx-proxy-conf created
configmap/notification-application-grpc-conf created
configmap/notification-application-rest-conf created
configmap/notification-application-scheduler-conf created
configmap/notification-application-worker-conf created
configmap/notification-conf created
configmap/notification-database-conf created
configmap/plugin-application-grpc-conf created
configmap/plugin-application-rest-conf created
configmap/plugin-application-scheduler-conf created
configmap/plugin-application-worker-conf created
configmap/plugin-conf created
configmap/plugin-database-conf created
configmap/repository-application-grpc-conf created
configmap/repository-application-rest-conf created
configmap/repository-application-scheduler-conf created
configmap/repository-application-worker-conf created
configmap/repository-conf created
configmap/repository-database-conf created
configmap/search-application-grpc-conf created
configmap/search-application-rest-conf created
configmap/search-application-scheduler-conf created
configmap/search-application-worker-conf created
configmap/search-conf created
configmap/search-database-conf created
configmap/secret-application-grpc-conf created
configmap/secret-application-rest-conf created
configmap/secret-application-scheduler-conf created
configmap/secret-application-worker-conf created
configmap/secret-conf created
configmap/secret-database-conf created
configmap/shared-conf created
configmap/spacectl-environment-conf created
configmap/statistics-application-grpc-conf created
configmap/statistics-application-rest-conf created
configmap/statistics-application-scheduler-conf created
configmap/statistics-application-worker-conf created
configmap/statistics-conf created
configmap/statistics-database-conf created
configmap/supervisor-application-scheduler-conf created
configmap/supervisor-conf created
Error from server (Conflict): error when applying patch:
{"data":{"ca.crt":"-----BEGIN CERTIFICATE-----\nMIIBdzCCAR2gAwIBAgIBADAKBggqhkjOPQQDAjAjMSEwHwYDVQQDDBhrM3Mtc2Vy\ndmVyLWNhQDE3Njc0MDk4NDgwHhcNMjYwMTAzMDMxMDQ4WhcNMzYwMTAxMDMxMDQ4\nWjAjMSEwHwYDVQQDDBhrM3Mtc2VydmVyLWNhQDE3Njc0MDk4NDgwWTATBgcqhkjO\nPQIBBggqhkjOPQMBBwNCAARQ6c6bKVfIyv8KLlw/e0rN+S7pXUaaciYcG8A+gxHB\nGfDovsBpk1JTHrVPaK4LqNWRxleiu+v49DjtulnIQdFUo0IwQDAOBgNVHQ8BAf8E\nBAMCAqQwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU+pdQyM2XeFSSkGZatPoW\nCNGouY4wCgYIKoZIzj0EAwIDSAAwRQIgfmT721MbK5CHbGdH3r1Qfk7sbOmlzpaQ\n0+NygLMUnywCIQD7FwD/MFWUq9l32kOo6EjZAqZWZWYWxhdLU0iwGdXEEQ==\n-----END CERTIFICATE-----\n"},"metadata":{"annotations":{"kubectl.kubernetes.io/last-applied-configuration":"{\"apiVersion\":\"v1\",\"data\":{\"ca.crt\":\"-----BEGIN CERTIFICATE-----\\nMIIBdzCCAR2gAwIBAgIBADAKBggqhkjOPQQDAjAjMSEwHwYDVQQDDBhrM3Mtc2Vy\\ndmVyLWNhQDE3Njc0MDk4NDgwHhcNMjYwMTAzMDMxMDQ4WhcNMzYwMTAxMDMxMDQ4\\nWjAjMSEwHwYDVQQDDBhrM3Mtc2VydmVyLWNhQDE3Njc0MDk4NDgwWTATBgcqhkjO\\nPQIBBggqhkjOPQMBBwNCAARQ6c6bKVfIyv8KLlw/e0rN+S7pXUaaciYcG8A+gxHB\\nGfDovsBpk1JTHrVPaK4LqNWRxleiu+v49DjtulnIQdFUo0IwQDAOBgNVHQ8BAf8E\\nBAMCAqQwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU+pdQyM2XeFSSkGZatPoW\\nCNGouY4wCgYIKoZIzj0EAwIDSAAwRQIgfmT721MbK5CHbGdH3r1Qfk7sbOmlzpaQ\\n0+NygLMUnywCIQD7FwD/MFWUq9l32kOo6EjZAqZWZWYWxhdLU0iwGdXEEQ==\\n-----END CERTIFICATE-----\\n\"},\"kind\":\"ConfigMap\",\"metadata\":{\"annotations\":{\"kubernetes.io/description\":\"Contains a CA bundle that can be used to verify the kube-apiserver when using internal endpoints such as the internal service IP or kubernetes.default.svc. No other usage is guaranteed across distributions of Kubernetes clusters.\"},\"creationTimestamp\":\"2026-01-03T03:11:45Z\",\"name\":\"kube-root-ca.crt\",\"namespace\":\"cloudforet\",\"resourceVersion\":\"729\",\"uid\":\"9eb477de-e019-4c53-bd80-6168fddb487d\"}}\n"},"creationTimestamp":"2026-01-03T03:11:45Z","resourceVersion":"729","uid":"9eb477de-e019-4c53-bd80-6168fddb487d"}}
to:
Resource: "/v1, Resource=configmaps", GroupVersionKind: "/v1, Kind=ConfigMap"
Name: "kube-root-ca.crt", Namespace: "cloudforet"
for: "cloudforet-configmaps.yaml": error when patching "cloudforet-configmaps.yaml": Operation cannot be fulfilled on configmaps "kube-root-ca.crt": the object has been modified; please apply your changes to the latest version and try again
secret/cloudforet-tls created
secret/dockerhub-secret created
secret/sh.helm.release.v1.cloudforet.v1 created
secret/sh.helm.release.v1.cloudforet.v2 created
secret/sh.helm.release.v1.cloudforet.v3 created
Warning: resource configmaps/kube-root-ca.crt is missing the kubectl.kubernetes.io/last-applied-configuration annotation which is required by kubectl apply. kubectl apply should only be used on resources created declaratively by either kubectl create --save-config or kubectl apply. The missing annotation will be patched automatically.
configmap/supervisor-application-scheduler-conf created
configmap/supervisor-conf created
Error from server (Conflict): error when applying patch:
{"data":{"ca.crt":"-----BEGIN CERTIFICATE-----\nMIIBdzCCAR2gAwIBAgIBADAKBggqhkjOPQQDAjAjMSEwHwYDVQQDDBhrM3Mtc2Vy\ndmVyLWNhQDE3Njc0MDk4NDgwHhcNMjYwMTAzMDMxMDQ4WhcNMzYwMTAxMDMxMDQ4\nWjAjMSEwHwYDVQQDDBhrM3Mtc2VydmVyLWNhQDE3Njc0MDk4NDgwWTATBgcqhkjO\nPQIBBggqhkjOPQMBBwNCAARQ6c6bKVfIyv8KLlw/e0rN+S7pXUaaciYcG8A+gxHB\nGfDovsBpk1JTHrVPaK4LqNWRxleiu+v49DjtulnIQdFUo0IwQDAOBgNVHQ8BAf8E\nBAMCAqQwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU+pdQyM2XeFSSkGZatPoW\nCNGouY4wCgYIKoZIzj0EAwIDSAAwRQIgfmT721MbK5CHbGdH3r1Qfk7sbOmlzpaQ\n0+NygLMUnywCIQD7FwD/MFWUq9l32kOo6EjZAqZWZWYWxhdLU0iwGdXEEQ==\n-----END CERTIFICATE-----\n"},"metadata":{"annotations":{"kubectl.kubernetes.io/last-applied-configuration":"{\"apiVersion\":\"v1\",\"data\":{\"ca.crt\":\"-----BEGIN CERTIFICATE-----\\nMIIBdzCCAR2gAwIBAgIBADAKBggqhkjOPQQDAjAjMSEwHwYDVQQDDBhrM3Mtc2Vy\\ndmVyLWNhQDE3Njc0MDk4NDgwHhcNMjYwMTAzMDMxMDQ4WhcNMzYwMTAxMDMxMDQ4\\nWjAjMSEwHwYDVQQDDBhrM3Mtc2VydmVyLWNhQDE3Njc0MDk4NDgwWTATBgcqhkjO\\nPQIBBggqhkjOPQMBBwNCAARQ6c6bKVfIyv8KLlw/e0rN+S7pXUaaciYcG8A+gxHB\\nGfDovsBpk1JTHrVPaK4LqNWRxleiu+v49DjtulnIQdFUo0IwQDAOBgNVHQ8BAf8E\\nBAMCAqQwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU+pdQyM2XeFSSkGZatPoW\\nCNGouY4wCgYIKoZIzj0EAwIDSAAwRQIgfmT721MbK5CHbGdH3r1Qfk7sbOmlzpaQ\\n0+NygLMUnywCIQD7FwD/MFWUq9l32kOo6EjZAqZWZWYWxhdLU0iwGdXEEQ==\\n-----END CERTIFICATE-----\\n\"},\"kind\":\"ConfigMap\",\"metadata\":{\"annotations\":{\"kubernetes.io/description\":\"Contains a CA bundle that can be used to verify the kube-apiserver when using internal endpoints such as the internal service IP or kubernetes.default.svc. No other usage is guaranteed across distributions of Kubernetes clusters.\"},\"creationTimestamp\":\"2026-01-03T03:11:45Z\",\"name\":\"kube-root-ca.crt\",\"namespace\":\"cloudforet-plugin\",\"resourceVersion\":\"731\",\"uid\":\"d37abcf7-e48b-4222-b6e5-b6f3e99f9d8b\"}}\n"},"creationTimestamp":"2026-01-03T03:11:45Z","resourceVersion":"731","uid":"d37abcf7-e48b-4222-b6e5-b6f3e99f9d8b"}}
to:
Resource: "/v1, Resource=configmaps", GroupVersionKind: "/v1, Kind=ConfigMap"
Name: "kube-root-ca.crt", Namespace: "cloudforet-plugin"
for: "cloudforet-plugin-configmaps.yaml": error when patching "cloudforet-plugin-configmaps.yaml": Operation cannot be fulfilled on configmaps "kube-root-ca.crt": the object has been modified; please apply your changes to the latest version and try again
error: no objects passed to apply
Restoring deployments and services...
deployment.apps/board created
deployment.apps/config created
deployment.apps/console created
deployment.apps/console-api created
deployment.apps/console-api-v2-rest created
deployment.apps/cost-analysis created
deployment.apps/cost-analysis-scheduler created
deployment.apps/cost-analysis-worker created
deployment.apps/dashboard created
deployment.apps/file-manager created
deployment.apps/file-manager-rest created
deployment.apps/identity created
deployment.apps/identity-scheduler created
deployment.apps/identity-worker created
deployment.apps/inventory created
deployment.apps/inventory-scheduler created
deployment.apps/inventory-worker created
deployment.apps/mongodb created
deployment.apps/monitoring created
deployment.apps/monitoring-rest created
deployment.apps/monitoring-scheduler created
deployment.apps/monitoring-worker created
deployment.apps/notification created
deployment.apps/notification-scheduler created
deployment.apps/notification-worker created
deployment.apps/plugin created
deployment.apps/plugin-scheduler created
deployment.apps/plugin-worker created
deployment.apps/redis created
deployment.apps/repository created
deployment.apps/search created
deployment.apps/secret created
deployment.apps/spacectl created
deployment.apps/statistics created
deployment.apps/statistics-scheduler created
deployment.apps/statistics-worker created
deployment.apps/supervisor-scheduler created
service/board created
service/config created
service/console created
service/console-api created
service/console-api-v2-rest created
service/cost-analysis created
service/dashboard created
service/file-manager created
service/file-manager-rest created
service/identity created
service/inventory created
service/mongodb created
service/monitoring created
service/monitoring-rest created
service/notification created
service/plugin created
service/redis created
service/repository created
service/search created
service/secret created
service/statistics created
deployment.apps/plugin-aws-ec2-inven-collector-rrzecgirtquoetbl created
service/plugin-aws-ec2-inven-collector-rrzecgirtquoetbl created
Waiting for MongoDB to be ready...





^CRestoring MongoDB data...
Restoring to MongoDB pod: mongodb-64fd57dd9d-7csq4
Error from server (BadRequest): pod mongodb-64fd57dd9d-7csq4 does not have a host assigned
MongoDB restore completed!

Restore completed! Checking pod status...
NAME                                      READY   STATUS              RESTARTS   AGE
board-5687775b85-h2f4d                    0/1     ContainerCreating   0          102s
config-5c8d9cbc5c-cs9c6                   0/1     ContainerCreating   0          102s
console-869b584bbf-r8dk5                  1/1     Running             0          102s
console-api-77779f48b5-95bmm              0/2     ContainerCreating   0          102s
console-api-v2-rest-77c5df5f6d-wtbs6      0/2     ContainerCreating   0          101s
cost-analysis-759c44b977-hggkd            0/1     ContainerCreating   0          101s
cost-analysis-scheduler-b86464866-v42zj   0/1     ContainerCreating   0          101s
cost-analysis-worker-6874fb855f-sjnn4     0/1     ContainerCreating   0          101s
dashboard-657b4b8745-wtmth                0/1     ContainerCreating   0          101s
file-manager-bd77d75fc-2j6kf              1/1     Running             0          101s
file-manager-rest-5db687c9b4-dvkdl        2/2     Running             0          100s
identity-645f44b79-wrqd6                  0/1     ContainerCreating   0          100s
identity-scheduler-64d6b5d56b-9vzb6       0/1     ContainerCreating   0          100s
identity-worker-695f746bf5-6vqnd          0/1     ContainerCreating   0          100s
inventory-686665944-vl9qx                 0/1     ContainerCreating   0          100s
inventory-scheduler-bcb6c6bbb-zwqft       0/1     ContainerCreating   0          99s
inventory-worker-6fbdc69d95-jnpgg         0/1     ContainerCreating   0          99s
mongodb-64fd57dd9d-7csq4                  0/1     Pending             0          99s
monitoring-77d4fc7779-9lctk               0/1     ContainerCreating   0          98s
monitoring-rest-7c694c69d8-dxzg2          0/2     ContainerCreating   0          98s
monitoring-scheduler-554cb6db8d-lqs98     0/1     ContainerCreating   0          98s
monitoring-worker-5d74b6fcd6-d444g        0/1     ContainerCreating   0          98s
notification-6b77b5fbb4-kg4fm             0/1     ContainerCreating   0          98s
notification-scheduler-67c4c4bf4-zm2mf    0/1     ContainerCreating   0          97s
notification-worker-79464566d9-v2bsq      0/1     ContainerCreating   0          97s
plugin-7c68b948f5-2ft45                   0/1     ContainerCreating   0          97s
plugin-scheduler-7db47bfdb8-pxjt8         0/1     ContainerCreating   0          97s
plugin-worker-6977f7f577-g5wrn            0/1     ContainerCreating   0          97s
redis-76dbfbf6d6-mlhzj                    1/1     Running             0          97s
repository-6c48b54986-rbvvb               0/1     ContainerCreating   0          96s
search-89fb5fff9-6n9td                    0/1     ImagePullBackOff    0          96s
secret-c46996684-jzbhb                    0/1     ContainerCreating   0          96s
spacectl-7dd4cc5848-hpk9v                 0/1     ContainerCreating   0          96s
statistics-cb79ddcfb-cmnrt                0/1     ContainerCreating   0          95s
statistics-scheduler-7db9f46658-t2qrw     0/1     ContainerCreating   0          95s
statistics-worker-7fb7bd948f-qk7mg        0/1     ContainerCreating   0          95s
supervisor-scheduler-7dc465c7df-wcdkd     0/2     ContainerCreating   0          95s
NAME                                                              READY   STATUS              RESTARTS   AGE
plugin-aws-ec2-inven-collector-rrzecgirtquoetbl-5c75566dc5tpnzg   0/1     ContainerCreating   0          94s


