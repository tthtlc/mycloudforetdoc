

kubectl get deployment supervisor-scheduler -n cloudforet-plugin -o yaml > supervisor_sched_deployment.yaml

### change the namespace to without plugin

ubuntu@instance-20251028-1358:~/tcy$ vi /tmp/schedsuper.out 
ubuntu@instance-20251028-1358:~/tcy$ kubectl  apply -f /tmp/schedsuper.out 
deployment.apps/supervisor-scheduler create


kubectl get cm -n cloudforet-plugin 
NAME                                    DATA   AGE
kube-root-ca.crt                        1      2d20h
shared-conf                             1      2d19h
supervisor-application-scheduler-conf   1      2d20h
supervisor-conf                         1      101m

kubectl get cm shared-conf  -n cloudforet-plugin -o yaml > /tmp/share.out

kubectl get cm shared-conf  -n cloudforet-plugin -o yaml > /tmp/share.yaml

kubectl get cm supervisor-application-scheduler-conf  -n cloudforet-plugin -o yaml > /tmp/scheduler.yaml

kubectl get cm supervisor-application-scheduler-conf  -n cloudforet-plugin -o yaml > /tmp/scheduler.yaml^C

ubuntu@instance-20251028-1358:~/tcy$ vi /tmp/scheduler.yaml 
ubuntu@instance-20251028-1358:~/tcy$ kubectl apply -f /tmp/scheduler.yaml 
configmap/supervisor-application-scheduler-conf created
ubuntu@instance-20251028-1358:~/tcy$ 

kubectl get cm supervisor-conf  -n cloudforet-plugin -o yaml > /tmp/super.yaml
ubuntu@instance-20251028-1358:~/tcy$ vi /tmp/super.yaml 
ubuntu@instance-20251028-1358:~/tcy$ kubectl apply -f /tmp/super 
error: the path "/tmp/super" does not exist
ubuntu@instance-20251028-1358:~/tcy$ kubectl apply -f /tmp/super.yaml 

