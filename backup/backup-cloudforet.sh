#!/bin/bash

# Cloudforet Kubernetes Backup Script
# This script exports all Kubernetes resources and MongoDB data

BACKUP_DIR="cloudforet-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting Cloudforet backup to $BACKUP_DIR..."

# 1. Backup Kubernetes Resources
echo "Backing up Kubernetes resources..."

# Export namespaces
kubectl get namespace cloudforet -o yaml > "$BACKUP_DIR/namespace-cloudforet.yaml"
kubectl get namespace cloudforet-plugin -o yaml > "$BACKUP_DIR/namespace-cloudforet-plugin.yaml"

# Export all resources in cloudforet namespace
echo "Exporting cloudforet namespace resources..."
kubectl get all -n cloudforet -o yaml > "$BACKUP_DIR/cloudforet-all-resources.yaml"
kubectl get configmaps -n cloudforet -o yaml > "$BACKUP_DIR/cloudforet-configmaps.yaml"
kubectl get secrets -n cloudforet -o yaml > "$BACKUP_DIR/cloudforet-secrets.yaml"
kubectl get ingress -n cloudforet -o yaml > "$BACKUP_DIR/cloudforet-ingress.yaml" 2>/dev/null || true

# Export all resources in cloudforet-plugin namespace
echo "Exporting cloudforet-plugin namespace resources..."
kubectl get all -n cloudforet-plugin -o yaml > "$BACKUP_DIR/cloudforet-plugin-all-resources.yaml"
kubectl get configmaps -n cloudforet-plugin -o yaml > "$BACKUP_DIR/cloudforet-plugin-configmaps.yaml"
kubectl get secrets -n cloudforet-plugin -o yaml > "$BACKUP_DIR/cloudforet-plugin-secrets.yaml"

# Export individual resource types for easier restoration
echo "Exporting individual resource types..."
for resource in deployments services configmaps secrets
do
    kubectl get $resource -n cloudforet -o yaml > "$BACKUP_DIR/cloudforet-$resource.yaml"
    kubectl get $resource -n cloudforet-plugin -o yaml > "$BACKUP_DIR/cloudforet-plugin-$resource.yaml"
done

# 2. Backup MongoDB Data
echo "Backing up MongoDB database..."
MONGODB_POD=$(kubectl get pods -n cloudforet -l app.kubernetes.io/name=mongodb -o jsonpath='{.items[0].metadata.name}')

if [ -n "$MONGODB_POD" ]; then
    echo "MongoDB pod: $MONGODB_POD"

    # MongoDB credentials (from mongodb-user-conf ConfigMap)
    MONGO_USER="admin"
    MONGO_PASS="password"

    # Get list of databases
    kubectl exec -n cloudforet "$MONGODB_POD" -- mongosh --quiet -u "$MONGO_USER" -p "$MONGO_PASS" --authenticationDatabase admin --eval "db.adminCommand('listDatabases')" > "$BACKUP_DIR/mongodb-databases-list.txt"

    # Dump all databases
    kubectl exec -n cloudforet "$MONGODB_POD" -- mongodump --username="$MONGO_USER" --password="$MONGO_PASS" --authenticationDatabase=admin --archive --gzip > "$BACKUP_DIR/mongodb-dump.archive.gz"

    echo "MongoDB backup completed: mongodb-dump.archive.gz (size: $(du -h $BACKUP_DIR/mongodb-dump.archive.gz | cut -f1))"
else
    echo "Warning: MongoDB pod not found!"
fi

# 3. Create a restore script
echo "Creating restore script..."
cat > "$BACKUP_DIR/restore-cloudforet.sh" << 'RESTORE_SCRIPT'
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

    # MongoDB credentials (from mongodb-user-conf ConfigMap)
    MONGO_USER="admin"
    MONGO_PASS="password"

    kubectl exec -n cloudforet "$MONGODB_POD" -i -- mongorestore --username="$MONGO_USER" --password="$MONGO_PASS" --authenticationDatabase=admin --archive --gzip < mongodb-dump.archive.gz
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
RESTORE_SCRIPT

chmod +x "$BACKUP_DIR/restore-cloudforet.sh"

# 4. Create backup metadata
cat > "$BACKUP_DIR/backup-info.txt" << INFO
Cloudforet Kubernetes Backup
Created: $(date)
Hostname: $(hostname)
Kubernetes Version: $(kubectl version --short 2>/dev/null || kubectl version)

Namespaces backed up:
- cloudforet
- cloudforet-plugin

Components:
- Kubernetes manifests (deployments, services, configmaps, secrets)
- MongoDB database dump

To restore on a new machine:
1. Copy this entire directory to the new machine
2. Ensure kubectl is configured to connect to the target cluster
3. Run: ./restore-cloudforet.sh
INFO

echo ""
echo "=================================================="
echo "Backup completed successfully!"
echo "Location: $BACKUP_DIR"
echo "=================================================="
echo ""
echo "Backup contents:"
ls -lh "$BACKUP_DIR"
echo ""
echo "To restore on another machine:"
echo "1. Copy the '$BACKUP_DIR' directory to the new machine"
echo "2. Ensure kubectl is configured on the new machine"
echo "3. Run: cd $BACKUP_DIR && ./restore-cloudforet.sh"
echo ""

# Create a compressed archive
echo "Creating compressed archive..."
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
echo "Compressed backup: ${BACKUP_DIR}.tar.gz"
echo "Size: $(du -h ${BACKUP_DIR}.tar.gz | cut -f1)"
