#!/bin/bash
set -e

# If kubeconfig exists, patch it for kind cluster access from Docker
if [ -f "/root/.kube/config" ]; then
    echo "Patching kubeconfig for Docker network access..."

    # Create a writable copy
    cp /root/.kube/config /tmp/kubeconfig

    # Replace localhost:53773 with kind container internal address
    # kind exposes the API server on port 6443 internally
    sed -i 's|https://127.0.0.1:[0-9]*|https://dev-control-plane:6443|g' /tmp/kubeconfig

    # Update the K8S_CONFIG_PATH to use the patched config
    export K8S_CONFIG_PATH=/tmp/kubeconfig

    echo "Kubeconfig patched. Using dev-control-plane:6443 for API server"
fi

# Execute the main command
exec "$@"
