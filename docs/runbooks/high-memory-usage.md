# High Memory Usage Troubleshooting

## Symptoms

- Pod evicted due to memory pressure
- OOMKilled status on containers
- Node memory pressure warnings
- Application performance degradation

## Diagnosis

### 1. Check Current Memory Usage

```bash
# Check pod memory usage
kubectl top pods -n <namespace>

# Check node memory usage
kubectl top nodes

# Get detailed pod resource info
kubectl describe pod <pod-name> -n <namespace>
```

### 2. Check Pod Events

```bash
# Look for OOMKilled or eviction events
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>

# Check for node pressure events
kubectl get events -n <namespace> --field-selector reason=Evicted
```

### 3. Analyze Memory Patterns

```bash
# Get pod logs to identify memory-intensive operations
kubectl logs <pod-name> -n <namespace> --tail=1000

# Check if memory leak is present (increasing over time)
kubectl top pod <pod-name> -n <namespace>
# Run multiple times and compare
```

## Common Causes & Solutions

### 1. Memory Leak in Application

**Symptoms:**
- Memory usage steadily increases over time
- Never returns to baseline
- Eventually hits limit and crashes

**Resolution:**
- Review application code for memory leaks
- Check for unclosed connections or file handles
- Look for unbounded caches or collections
- Use memory profiling tools

**Fix:**
- Implement proper resource cleanup
- Set cache size limits
- Use memory profiling to identify leaks
- Consider restarting pods periodically as temporary measure

### 2. Insufficient Memory Limits

**Symptoms:**
- Application legitimately needs more memory
- OOMKilled during normal operation
- Requests and limits too low for workload

**Resolution:**
```bash
# Check current limits
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources}'
```

**Fix:**
```yaml
# Increase memory limits in deployment
resources:
  requests:
    memory: "512Mi"  # Kubernetes scheduler uses this
    cpu: "250m"
  limits:
    memory: "1Gi"    # Container killed if exceeded
    cpu: "500m"
```

**Best Practices:**
- Set requests = typical usage
- Set limits = peak usage + buffer (20-30%)
- Monitor actual usage to right-size

### 3. Memory-Intensive Operations

**Symptoms:**
- Spikes during specific operations
- Batch jobs or data processing
- Large file uploads/downloads

**Resolution:**
- Identify which operations cause spikes
- Review logs during high usage periods
- Profile application during heavy operations

**Fix:**
- Process data in chunks/streams
- Implement pagination for large datasets
- Use disk for temporary storage instead of memory
- Scale horizontally for batch jobs

### 4. JVM Heap Size Misconfiguration

**Symptoms:**
- Java application OOMKilled
- Heap size not aligned with container limits
- GC overhead limit exceeded

**Resolution:**
```bash
# Check JVM settings in pod
kubectl exec <pod-name> -n <namespace> -- java -XX:+PrintFlagsFinal -version | grep HeapSize
```

**Fix:**
```yaml
env:
  - name: JAVA_OPTS
    value: "-Xms512m -Xmx1g -XX:+UseG1GC"
  # Set max heap to ~75% of container limit
  # Container limit 1.5Gi -> heap max 1Gi
```

### 5. Too Many Pods on Node

**Symptoms:**
- Node under memory pressure
- Multiple pods evicted
- Node memory saturated

**Resolution:**
```bash
# Check node capacity
kubectl describe node <node-name>

# List all pods on node
kubectl get pods --all-namespaces -o wide --field-selector spec.nodeName=<node-name>

# Sum memory requests per node
kubectl get pods --all-namespaces -o jsonpath='{range .items[?(@.spec.nodeName=="<node-name>")]}{.metadata.name}{"\t"}{.spec.containers[*].resources.requests.memory}{"\n"}{end}'
```

**Fix:**
- Add more nodes to cluster
- Distribute pods more evenly (anti-affinity rules)
- Right-size pod resource requests
- Implement pod disruption budgets

### 6. Memory Not Released (Caching)

**Symptoms:**
- Memory usage high but stable
- Application caching aggressively
- Not actually a problem if no OOM

**Resolution:**
- Verify it's actually an issue (check for OOMs)
- Some caching is beneficial for performance

**Fix:**
- Configure cache eviction policies
- Set max cache sizes
- Use external cache (Redis) for large datasets
- Tune cache TTL values

## Monitoring & Alerts

### Set up Monitoring

```bash
# Using kubectl top (basic)
kubectl top pods -n <namespace> --sort-by=memory

# Set up prometheus queries (advanced)
# Example: Memory usage > 80% of limit
container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
```

### Recommended Alerts

1. **Pod OOMKilled** - immediate alert
2. **Memory usage > 80% of limit** - warning
3. **Memory usage growing steadily** - warning (potential leak)
4. **Node memory pressure** - critical

## Prevention

1. **Load Testing**
   - Test with realistic data volumes
   - Identify memory requirements before production

2. **Resource Planning**
   - Set appropriate requests and limits
   - Monitor actual usage over time
   - Right-size based on metrics

3. **Application Best Practices**
   - Implement streaming for large data
   - Use pagination
   - Proper resource cleanup
   - Bounded caches

4. **Horizontal Scaling**
   - Use HPA (Horizontal Pod Autoscaler)
   - Scale out instead of up when possible

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
```

5. **Regular Reviews**
   - Monthly resource usage reviews
   - Identify trends and adjust
   - Decommission unused resources

## Related Runbooks

- Pod CrashLoopBackOff Resolution
- Node Resource Pressure
- Application Performance Troubleshooting
