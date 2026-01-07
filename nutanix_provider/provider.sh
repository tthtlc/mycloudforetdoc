
kubectl exec -n cloudforet deploy/spacectl -- spacectl list identity.Provider


exit
###delete
##kubectl exec -n cloudforet deploy/spacectl -- spacectl exec delete identity.Provider -p provider=nutanix
kubectl exec -n cloudforet deploy/spacectl -- spacectl exec create identity.Provider -f provider.yaml
kubectl exec -n cloudforet deploy/spacectl -- spacectl exec list identity.Provider
kubectl exec -n cloudforet deploy/spacectl -- spacectl list identity.Provider

