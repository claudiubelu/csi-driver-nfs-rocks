#
# Copyright 2024 Canonical, Ltd.
#

import logging
import pathlib

from k8s_test_harness import harness
from k8s_test_harness.util import constants, env_util, exec_util, k8s_util

LOG = logging.getLogger(__name__)

DIR = pathlib.Path(__file__).absolute().parent
MANIFESTS_DIR = DIR / ".." / "templates"


def _get_nfsplugin_csi_helm_cmd(version: str):
    rock = env_util.get_build_meta_info_for_rock_version("nfsplugin", version, "amd64")

    images = [
        k8s_util.HelmImage(rock.image, subitem="nfs"),
    ]

    set_configs = [
        "externalSnapshotter.enabled=true",
    ]

    return k8s_util.get_helm_install_command(
        "csi-driver-nfs",
        "csi-driver-nfs",
        repository="https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts",
        chart_version="v4.7.0",
        images=images,
        set_configs=set_configs,
    )


def test_nfsplugin_integration(function_instance: harness.Instance):
    helm_command = _get_nfsplugin_csi_helm_cmd("4.7.0")
    function_instance.exec(helm_command)

    # wait for all the components to become active.
    k8s_util.wait_for_daemonset(function_instance, "csi-nfs-node", "kube-system")
    k8s_util.wait_for_deployment(function_instance, "csi-nfs-controller", "kube-system")
    k8s_util.wait_for_deployment(
        function_instance, "snapshot-controller", "kube-system"
    )

    # call the nfsplugin's liveness probes to check that they're running as intended.
    for port in [29652, 29653]:
        # It has hostNetwork=true, which means that curling localhost should work.
        exec_util.stubbornly(retries=5, delay_s=5).on(function_instance).exec(
            ["curl", f"http://localhost:{port}/healthz"]
        )

    # Deploy a NFS server and an nginx Pod with a NFS volume attached.
    for item in ["nfs-server.yaml", "nginx-pod.yaml"]:
        manifest = MANIFESTS_DIR / item
        function_instance.exec(
            ["k8s", "kubectl", "apply", "-f", "-"],
            input=pathlib.Path(manifest).read_bytes(),
        )

    # Expect the Pod to become ready, and that it has the volume attached.
    k8s_util.wait_for_deployment(function_instance, "nfs-server")
    k8s_util.wait_for_resource(
        function_instance,
        "pod",
        "nginx-nfs-example",
        condition=constants.K8S_CONDITION_READY,
    )

    process = function_instance.exec(
        [
            "k8s",
            "kubectl",
            "exec",
            "nginx-nfs-example",
            "--",
            "bash",
            "-c",
            "findmnt /var/www -o TARGET,SOURCE,FSTYPE",
        ],
        capture_output=True,
        text=True,
    )
    assert "/var/www nfs-server.default.svc.cluster.local:/ nfs4" in process.stdout
