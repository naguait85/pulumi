import * as pulumi from "@pulumi/pulumi";
import * as k8s from "@pulumi/kubernetes";

const pulumiConfig = new pulumi.Config();

// Existing Pulumi stack reference in the format:
// <organization>/<project>/<stack> e.g. "myUser/myProject/dev"
const clusterStackRef = new pulumi.StackReference(pulumiConfig.require("clusterStackRef"));

// Declare a Kubernetes Provider that can talk to our EKS Infrastructure
const provider = new k8s.Provider("k8s", { kubeconfig: clusterStackRef.getOutput("kubeconfig") });

// Declare a Namespace in which to deploy argocd
const name = "argocd"
const ns = new k8s.core.v1.Namespace("argocd-ns", {
    metadata: { name: name },
}, { provider });

// Deploy the ArgoCD Helm Chart
const argocd = new k8s.helm.v2.Chart("argocd",
    {
        namespace: ns.metadata.name,
        chart: "argo-cd",
        fetchOpts: { repo: "https://argoproj.github.io/argo-helm" },
        values: {
            installCRDs: false,
            server: {
                service: {
                    type: 'LoadBalancer',
                },
            }
        },
        // The helm chart is using a deprecated apiVersion,
        // So let's transform it
        transformations: [
            (obj: any) => {
                if (obj.apiVersion == "extensions/v1beta1")  {
                    obj.apiVersion = "networking.k8s.io/v1beta1"
                }
            },
        ],
    },
    { providers: { kubernetes: provider }},
);

// Export the URL of our ArgoCD Webserver and the Namespace in which ArgoCD has been deployed
export const argoNamespace = name;
export const url = argocd.getResourceProperty("v1/Service", `${name}/argocd-server`, "status").apply(status => status.loadBalancer.ingress[0].hostname)
