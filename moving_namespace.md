##
##kubectl get deployment supervisor-scheduler -n cloudforet-plugin -o yaml > supervisor_sched_deployment_before.yaml
##
##cat - <<EOF > /tmp/tmp.patch
##- supervisor_sched_deployment_before.yaml	2025-12-30 09:30:01.824805724 +0000
##+++ after.yaml	2025-12-30 09:33:31.641094938 +0000
##@@ -15,7 +15,7 @@ metadata:
##     helm.sh/chart: supervisor-1.1.15
##     spaceone.service: supervisor
##   name: supervisor-scheduler
##-  namespace: cloudforet-plugin
##+  namespace: cloudforet
##   resourceVersion: "139079"
##   uid: eea907e4-107c-4119-be29-61e96efa3cb1
## spec:
##EOF
##
##patch --dry-run -p0 supervisor_sched_deployment_before.yaml </tmp/tmp.patch

kubectl get deployment supervisor-scheduler -n cloudforet-plugin -o yaml | sed 's/namespace: cloudforet-plugin/namespace: cloudforet/' > /tmp/tmpafter.yaml

kubectl apply -f /tmp/tmpafter.yaml

kubectl describe pod supervisor-scheduler-7dc465c7df-wz648 -n cloudforet

Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason       Age                From               Message
  ----     ------       ----               ----               -------
  Normal   Scheduled    98s                default-scheduler  Successfully assigned cloudforet/supervisor-scheduler-7dc465c7df-wz648 to k3s-server
  Warning  FailedMount  34s (x8 over 98s)  kubelet            MountVolume.SetUp failed for volume "default-conf" : configmap "supervisor-conf" not found
  Warning  FailedMount  34s (x8 over 98s)  kubelet            MountVolume.SetUp failed for volume "application-conf" : configmap "supervisor-application-scheduler-conf" not found

kubectl get cm -n cloudforet-plugin

NAME                                    DATA   AGE
kube-root-ca.crt                        1      3d22h
shared-conf                             1      3d21h
supervisor-application-scheduler-conf   1      3d14h
supervisor-conf                         1      3d14h

kubectl get cm supervisor-application-scheduler-conf -n cloudforet-plugin -o yaml > /tmp/super_app_sched_conf.yaml

Modify the yaml file:

ubuntu@instance-20251024-1642:~/tcy$ diff -Nurp bef.yaml after.yaml 
--- bef.yaml	2025-12-30 06:53:52.158798035 +0000
+++ after.yaml	2025-12-30 06:54:01.736903076 +0000
@@ -30,6 +30,6 @@ metadata:
   labels:
     app.kubernetes.io/managed-by: Helm
   name: supervisor-application-scheduler-conf
-  namespace: cloudforet-plugin
+  namespace: cloudforet
   resourceVersion: "16939"
   uid: a80e7d98-e526-4e0a-b84f-c01c9a925028

kubectl get cm supervisor-conf -n cloudforet-plugin -o yaml > supervisor_conf.yaml
Modify the yaml file:

ubuntu@instance-20251024-1642:~/tcy$ diff -Nurp bef.yaml after.yaml 
--- bef.yaml	2025-12-30 06:57:24.320395365 +0000
+++ after.yaml	2025-12-30 06:57:14.776019928 +0000
@@ -69,6 +69,6 @@ metadata:
   labels:
     app.kubernetes.io/managed-by: Helm
   name: supervisor-conf
-  namespace: cloudforet-plugin
+  namespace: cloudforet
   resourceVersion: "16940"
   uid: 5ce0fc9d-a766-46bc-9640-4e7542af24aa

###Delete from plugin namespace:

kubectl delete deployment/supervisor-scheduler -n cloudforet-plugin

###deelete from cloudforet and to be recreated automatically:

kubectl delete pod supervisor-scheduler-7dc465c7df-wz648 -n cloudforet
ubuntu@instance-20251024-1642:~/tcy$ 
