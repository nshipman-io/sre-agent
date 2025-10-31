# Example Kubernetes Manifests

Test resources for the SRE agent's delete functionality.

## Available Resources

- **example-pod.yaml** - Simple nginx pod
- **example-deployment.yaml** - Nginx deployment (2 replicas)
- **example-service.yaml** - ClusterIP service
- **example-configmap.yaml** - ConfigMap with nginx config

## Deploy Resources

```bash
# Deploy all
kubectl apply -f example-manifests/

# Or individually
kubectl apply -f example-manifests/example-pod.yaml
```

## Verify Deployment

```bash
kubectl get pods,deployments,services,configmaps -n default -l environment=test
```

## Test Agent Deletion

Ask the agent:
- "Delete the pod named test-nginx-pod in the default namespace"
- "Remove the deployment test-nginx-deployment from default"
- "Delete the service test-nginx-service"
- "Delete the configmap test-nginx-config"

## Clean Up

```bash
kubectl delete -f example-manifests/
```
