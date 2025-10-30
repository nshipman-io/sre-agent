# Pod CrashLoopBackOff Resolution

## Symptoms

- Pods in `CrashLoopBackOff` state
- Pods continuously restarting
- High restart count on containers

## Common Causes

### 1. Application Errors

**Symptoms:**
- Application exits immediately after start
- Error logs visible in pod logs

**Resolution:**
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Look for application errors, missing dependencies, configuration issues
```

**Fix:**
- Review application logs
- Check for missing environment variables
- Verify configuration files are mounted correctly
- Ensure application has proper startup logic

### 2. Insufficient Resources

**Symptoms:**
- OOMKilled in pod status
- Container exceeds memory limits

**Resolution:**
```bash
# Check pod resource usage
kubectl top pod <pod-name> -n <namespace>

# Describe pod to see resource limits
kubectl describe pod <pod-name> -n <namespace>
```

**Fix:**
```yaml
# Increase memory limits in deployment
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 3. Liveness Probe Failures

**Symptoms:**
- Healthy application but k8s keeps restarting it
- Liveness probe failures in events

**Resolution:**
```bash
# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Look for liveness probe failures
```

**Fix:**
- Adjust liveness probe `initialDelaySeconds` to allow app startup time
- Increase `timeoutSeconds` if probe is timing out
- Verify probe endpoint is correct and accessible

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30  # Increase if app needs more startup time
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### 4. Missing Dependencies

**Symptoms:**
- Application can't connect to database/external service
- Timeout errors in logs

**Resolution:**
```bash
# Check service endpoints
kubectl get endpoints -n <namespace>

# Test connectivity from pod
kubectl exec -it <pod-name> -n <namespace> -- ping <service-name>
kubectl exec -it <pod-name> -n <namespace> -- curl <service-url>
```

**Fix:**
- Ensure dependent services are running and healthy
- Verify network policies allow traffic
- Check service discovery configuration
- Verify DNS resolution

### 5. Image Pull Errors

**Symptoms:**
- ImagePullBackOff or ErrImagePull
- Cannot pull container image

**Resolution:**
```bash
# Check image pull status
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 Events
```

**Fix:**
- Verify image name and tag are correct
- Check image registry credentials
- Ensure registry is accessible from cluster
- Create/update imagePullSecrets if needed

## Prevention

1. **Implement proper health checks**
   - Use both liveness and readiness probes
   - Set appropriate timeouts and delays

2. **Set resource limits and requests**
   - Monitor actual resource usage
   - Set appropriate limits with headroom

3. **Proper error handling**
   - Graceful degradation when dependencies unavailable
   - Retry logic with exponential backoff

4. **Comprehensive logging**
   - Log startup sequence
   - Log connection attempts to dependencies
   - Structured logging for easy parsing

5. **Test in staging**
   - Test with realistic resource constraints
   - Test failure scenarios

## Related Commands

```bash
# Get pod status
kubectl get pods -n <namespace>

# Watch pod status
kubectl get pods -n <namespace> -w

# Get detailed pod information
kubectl describe pod <pod-name> -n <namespace>

# Get pod logs (current)
kubectl logs <pod-name> -n <namespace>

# Get pod logs (previous container)
kubectl logs <pod-name> -n <namespace> --previous

# Get logs from specific container
kubectl logs <pod-name> -c <container-name> -n <namespace>

# Execute command in pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Get events sorted by time
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```
