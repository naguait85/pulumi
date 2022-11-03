"""A Kubernetes Python Pulumi program"""

import pulumi
import pulumi_kubernetes as kubernetes
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs

# Create a K8s namespace.

istiosystem_namespace = kubernetes.core.v1.Namespace(
    "istio-system",
    metadata={
        "name": "istio-system",
    })
# label the namespace for istio sidecar
provider = kubernetes.Provider("provider", enable_server_side_apply=True)
istio_system = kubernetes.core.v1.NamespacePatch("istio_system", metadata=kubernetes.meta.v1.ObjectMetaPatchArgs(
    name="istio-system",
    labels={
        "istio-injection": "enabled",
    },
), opts=pulumi.ResourceOptions(provider=provider))

istiod = Release(
    "istiod",
    ReleaseArgs(
        chart="istiod",
        namespace= "istio-system",
        repository_opts=RepositoryOptsArgs(
            repo="https://istio-release.storage.googleapis.com/charts",
        ),

        skip_await=False))

istiogateway = Release(
    "gateway",
    ReleaseArgs(
        chart="gateway",
        namespace= "istio-system",
        repository_opts=RepositoryOptsArgs(
            repo="https://istio-release.storage.googleapis.com/charts",
        ),
    # version="4.2.5",
    skip_await =False))

kiali = Release(
    "kiali-server",
    ReleaseArgs(
        chart="kiali-server",
        namespace= "istio-system",
        repository_opts=RepositoryOptsArgs(
            repo="https://kiali.org/helm-charts",
        ),
    skip_await=False))

#release = Release("istio-helm", args=istiobase)

# We can look up resources once the release is installed. The release's
# status field is set once the installation completes, so this, combined
# with `skip_await=False` above, will wait to retrieve the Redis master
# ClusterIP until all resources in the Chart are available.
#status = release.status
#srv = Service.get("redis-master-svc",
#                  Output.concat(status.namespace, "/", status.name, "-master"))
#pulumi.export("redisMasterClusterIP", srv.spec.cluster_ip)
istio_system_prometheus_service_account = kubernetes.core.v1.ServiceAccount("istio_systemPrometheusServiceAccount",
    api_version="v1",
    kind="ServiceAccount",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        labels={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
            "chart": "prometheus-15.9.0",
            "heritage": "Helm",
        },
        name="prometheus",
        namespace="istio-system",
        annotations={},
    ))
istio_system_prometheus_config_map = kubernetes.core.v1.ConfigMap("istio_systemPrometheusConfigMap",
    api_version="v1",
    kind="ConfigMap",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        labels={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
            "chart": "prometheus-15.9.0",
            "heritage": "Helm",
        },
        name="prometheus",
        namespace="istio-system",
    ),
    data={
        "alerting_rules.yml": "{}\n",
        "alerts": "{}\n",
        "prometheus.yml": """global:
      evaluation_interval: 1m
      scrape_interval: 15s
      scrape_timeout: 10s
    rule_files:
    - /etc/config/recording_rules.yml
    - /etc/config/alerting_rules.yml
    - /etc/config/rules
    - /etc/config/alerts
    scrape_configs:
    - job_name: prometheus
      static_configs:
      - targets:
        - localhost:9090
    - bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      job_name: kubernetes-apiservers
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - action: keep
        regex: default;kubernetes;https
        source_labels:
        - __meta_kubernetes_namespace
        - __meta_kubernetes_service_name
        - __meta_kubernetes_endpoint_port_name
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
    - bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      job_name: kubernetes-nodes
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - replacement: kubernetes.default.svc:443
        target_label: __address__
      - regex: (.+)
        replacement: /api/v1/nodes/$1/proxy/metrics
        source_labels:
        - __meta_kubernetes_node_name
        target_label: __metrics_path__
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
    - bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      job_name: kubernetes-nodes-cadvisor
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - replacement: kubernetes.default.svc:443
        target_label: __address__
      - regex: (.+)
        replacement: /api/v1/nodes/$1/proxy/metrics/cadvisor
        source_labels:
        - __meta_kubernetes_node_name
        target_label: __metrics_path__
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
    - honor_labels: true
      job_name: kubernetes-service-endpoints
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scrape
      - action: drop
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scrape_slow
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_service_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_service_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_service_name
        target_label: service
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_node_name
        target_label: node
    - honor_labels: true
      job_name: kubernetes-service-endpoints-slow
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scrape_slow
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_service_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_service_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_service_name
        target_label: service
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_node_name
        target_label: node
      scrape_interval: 5m
      scrape_timeout: 30s
    - honor_labels: true
      job_name: prometheus-pushgateway
      kubernetes_sd_configs:
      - role: service
      relabel_configs:
      - action: keep
        regex: pushgateway
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_probe
    - honor_labels: true
      job_name: kubernetes-services
      kubernetes_sd_configs:
      - role: service
      metrics_path: /probe
      params:
        module:
        - http_2xx
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_probe
      - source_labels:
        - __address__
        target_label: __param_target
      - replacement: blackbox
        target_label: __address__
      - source_labels:
        - __param_target
        target_label: instance
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels:
        - __meta_kubernetes_namespace
        target_label: namespace
      - source_labels:
        - __meta_kubernetes_service_name
        target_label: service
    - honor_labels: true
      job_name: kubernetes-pods
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scrape
      - action: drop
        regex: true
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scrape_slow
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_pod_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_name
        target_label: pod
      - action: drop
        regex: Pending|Succeeded|Failed|Completed
        source_labels:
        - __meta_kubernetes_pod_phase
    - honor_labels: true
      job_name: kubernetes-pods-slow
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scrape_slow
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_pod_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_name
        target_label: pod
      - action: drop
        regex: Pending|Succeeded|Failed|Completed
        source_labels:
        - __meta_kubernetes_pod_phase
      scrape_interval: 5m
      scrape_timeout: 30s
""",
        "recording_rules.yml": "{}\n",
        "rules": "{}\n",
    })
prometheus_cluster_role = kubernetes.rbac.v1.ClusterRole("prometheusClusterRole",
    api_version="rbac.authorization.k8s.io/v1",
    kind="ClusterRole",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        labels={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
            "chart": "prometheus-15.9.0",
            "heritage": "Helm",
        },
        name="prometheus",
    ),
    rules=[
        kubernetes.rbac.v1.PolicyRuleArgs(
            api_groups=[""],
            resources=[
                "nodes",
                "nodes/proxy",
                "nodes/metrics",
                "services",
                "endpoints",
                "pods",
                "ingresses",
                "configmaps",
            ],
            verbs=[
                "get",
                "list",
                "watch",
            ],
        ),
        kubernetes.rbac.v1.PolicyRuleArgs(
            api_groups=[
                "extensions",
                "networking.k8s.io",
            ],
            resources=[
                "ingresses/status",
                "ingresses",
            ],
            verbs=[
                "get",
                "list",
                "watch",
            ],
        ),
        kubernetes.rbac.v1.PolicyRuleArgs(
            non_resource_urls=["/metrics"],
            verbs=["get"],
        ),
    ])
prometheus_cluster_role_binding = kubernetes.rbac.v1.ClusterRoleBinding("prometheusClusterRoleBinding",
    api_version="rbac.authorization.k8s.io/v1",
    kind="ClusterRoleBinding",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        labels={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
            "chart": "prometheus-15.9.0",
            "heritage": "Helm",
        },
        name="prometheus",
    ),
    subjects=[kubernetes.rbac.v1.SubjectArgs(
        kind="ServiceAccount",
        name="prometheus",
        namespace="istio-system",
    )],
    role_ref=kubernetes.rbac.v1.RoleRefArgs(
        api_group="rbac.authorization.k8s.io",
        kind="ClusterRole",
        name="prometheus",
    ))
istio_system_prometheus_service = kubernetes.core.v1.Service("istio_systemPrometheusService",
    api_version="v1",
    kind="Service",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        labels={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
            "chart": "prometheus-15.9.0",
            "heritage": "Helm",
        },
        name="prometheus",
        namespace="istio-system",
    ),
    spec=kubernetes.core.v1.ServiceSpecArgs(
        ports=[kubernetes.core.v1.ServicePortArgs(
            name="http",
            port=9090,
            protocol="TCP",
            target_port=9090,
        )],
        selector={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
        },
        session_affinity="None",
        type="ClusterIP",
    ))
istio_system_prometheus_deployment = kubernetes.apps.v1.Deployment("istio_systemPrometheusDeployment",
    api_version="apps/v1",
    kind="Deployment",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        labels={
            "component": "server",
            "app": "prometheus",
            "release": "prometheus",
            "chart": "prometheus-15.9.0",
            "heritage": "Helm",
        },
        name="prometheus",
        namespace="istio-system",
    ),
    spec=kubernetes.apps.v1.DeploymentSpecArgs(
        selector=kubernetes.meta.v1.LabelSelectorArgs(
            match_labels={
                "component": "server",
                "app": "prometheus",
                "release": "prometheus",
            },
        ),
        replicas=1,
        template=kubernetes.core.v1.PodTemplateSpecArgs(
            metadata=kubernetes.meta.v1.ObjectMetaArgs(
                labels={
                    "component": "server",
                    "app": "prometheus",
                    "release": "prometheus",
                    "chart": "prometheus-15.9.0",
                    "heritage": "Helm",
                    "sidecar.istio.io/inject": "false",
                },
            ),
            spec=kubernetes.core.v1.PodSpecArgs(
                enable_service_links=True,
                service_account_name="prometheus",
                containers=[
                    kubernetes.core.v1.ContainerArgs(
                        name="prometheus-server-configmap-reload",
                        image="jimmidyson/configmap-reload:v0.5.0",
                        image_pull_policy="IfNotPresent",
                        args=[
                            "--volume-dir=/etc/config",
                            "--webhook-url=http://127.0.0.1:9090/-/reload",
                        ],
                        resources=kubernetes.core.v1.ResourceRequirementsArgs(),
                        volume_mounts=[kubernetes.core.v1.VolumeMountArgs(
                            name="config-volume",
                            mount_path="/etc/config",
                            read_only=True,
                        )],
                    ),
                    kubernetes.core.v1.ContainerArgs(
                        name="prometheus-server",
                        image="prom/prometheus:v2.34.0",
                        image_pull_policy="IfNotPresent",
                        args=[
                            "--storage.tsdb.retention.time=15d",
                            "--config.file=/etc/config/prometheus.yml",
                            "--storage.tsdb.path=/data",
                            "--web.console.libraries=/etc/prometheus/console_libraries",
                            "--web.console.templates=/etc/prometheus/consoles",
                            "--web.enable-lifecycle",
                        ],
                        ports=[kubernetes.core.v1.ContainerPortArgs(
                            container_port=9090,
                        )],
                        readiness_probe=kubernetes.core.v1.ProbeArgs(
                            http_get=kubernetes.core.v1.HTTPGetActionArgs(
                                path="/-/ready",
                                port=9090,
                                scheme="HTTP",
                            ),
                            initial_delay_seconds=0,
                            period_seconds=5,
                            timeout_seconds=4,
                            failure_threshold=3,
                            success_threshold=1,
                        ),
                        liveness_probe=kubernetes.core.v1.ProbeArgs(
                            http_get=kubernetes.core.v1.HTTPGetActionArgs(
                                path="/-/healthy",
                                port=9090,
                                scheme="HTTP",
                            ),
                            initial_delay_seconds=30,
                            period_seconds=15,
                            timeout_seconds=10,
                            failure_threshold=3,
                            success_threshold=1,
                        ),
                        resources=kubernetes.core.v1.ResourceRequirementsArgs(),
                        volume_mounts=[
                            kubernetes.core.v1.VolumeMountArgs(
                                name="config-volume",
                                mount_path="/etc/config",
                            ),
                            kubernetes.core.v1.VolumeMountArgs(
                                name="storage-volume",
                                mount_path="/data",
                                sub_path="",
                            ),
                        ],
                    ),
                ],
                host_network=False,
                dns_policy="ClusterFirst",
                security_context=kubernetes.core.v1.PodSecurityContextArgs(
                    fs_group=65534,
                    run_as_group=65534,
                    run_as_non_root=True,
                    run_as_user=65534,
                ),
                termination_grace_period_seconds=300,
                volumes=[
                    kubernetes.core.v1.VolumeArgs(
                        name="config-volume",
                        config_map=kubernetes.core.v1.ConfigMapVolumeSourceArgs(
                            name="prometheus",
                        ),
                    ),
                    kubernetes.core.v1.VolumeArgs(
                        name="storage-volume",
                        empty_dir=kubernetes.core.v1.EmptyDirVolumeSourceArgs(),
                    ),
                ],
            ),
        ),
    ))
