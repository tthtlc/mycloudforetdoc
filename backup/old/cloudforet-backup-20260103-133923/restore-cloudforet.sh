#!/bin/bash

# Cloudforet Kubernetes Restore Script

echo "WARNING: This will restore Cloudforet on the current Kubernetes cluster."
echo "Make sure you are connected to the correct cluster!"
echo ""
kubectl cluster-info
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 1
fi

# 1. Create namespaces
echo "Creating namespaces..."
kubectl apply -f namespace-cloudforet.yaml
kubectl apply -f namespace-cloudforet-plugin.yaml

# 2. Restore secrets and configmaps first
echo "Restoring ConfigMaps and Secrets..."
kubectl apply -f cloudforet-configmaps.yaml
kubectl apply -f cloudforet-secrets.yaml
kubectl apply -f cloudforet-plugin-configmaps.yaml
kubectl apply -f cloudforet-plugin-secrets.yaml

# 3. Restore all other resources
echo "Restoring deployments and services..."
kubectl apply -f cloudforet-deployments.yaml
kubectl apply -f cloudforet-services.yaml
kubectl apply -f cloudforet-plugin-deployments.yaml
kubectl apply -f cloudforet-plugin-services.yaml

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mongodb -n cloudforet --timeout=300s

# 4. Restore MongoDB data
echo "Restoring MongoDB data..."
MONGODB_POD=$(kubectl get pods -n cloudforet -l app.kubernetes.io/name=mongodb -o jsonpath='{.items[0].metadata.name}')

if [ -n "$MONGODB_POD" ] && [ -f "mongodb-dump.archive.gz" ]; then
    echo "Restoring to MongoDB pod: $MONGODB_POD"
    kubectl exec -n cloudforet "$MONGODB_POD" -i -- mongorestore --archive --gzip < mongodb-dump.archive.gz
    echo "MongoDB restore completed!"
else
    echo "Warning: MongoDB pod not found or backup file missing!"
fi

echo ""
echo "Restore completed! Checking pod status..."
kubectl get pods -n cloudforet
kubectl get pods -n cloudforet-plugin

echo ""
echo "If some pods are not ready, give them a few minutes to start up."
