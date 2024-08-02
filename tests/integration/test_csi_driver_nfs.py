#
# Copyright 2024 Canonical, Ltd.
#

import logging

from k8s_test_harness import harness
from k8s_test_harness.util import env_util, k8s_util

LOG = logging.getLogger(__name__)

CSI_PROVISIONER_IMG = "ghcr.io/canonical/csi-provisioner:4.0.0-ck0"
LIVENESSPROBE_IMG = "ghcr.io/canonical/livenessprobe:2.12.0-ck0"
NODE_DRIVER_REGISTRAR_IMG = "ghcr.io/canonical/csi-node-driver-registrar:2.10.0-ck0"
SNAPSHOT_CONTROLLER_IMG = "ghcr.io/canonical/snapshot-controller:6.3.3-ck0"
SNAPSHOTTER_IMG = "ghcr.io/canonical/csi-snapshotter:6.3.3-ck0"


def _get_nfsplugin_csi_helm_cmd(version: str):
    rock = env_util.get_build_meta_info_for_rock_version("nfsplugin", version, "amd64")

    images = [
        k8s_util.HelmImage(rock.image, subitem="nfs"),
        k8s_util.HelmImage(CSI_PROVISIONER_IMG, subitem="csiProvisioner"),
        k8s_util.HelmImage(LIVENESSPROBE_IMG, subitem="livenessProbe"),
        k8s_util.HelmImage(NODE_DRIVER_REGISTRAR_IMG, subitem="nodeDriverRegistrar"),
        k8s_util.HelmImage(SNAPSHOT_CONTROLLER_IMG, subitem="externalSnapshotter"),
        k8s_util.HelmImage(SNAPSHOTTER_IMG, subitem="csiSnapshotter"),
    ]

    return k8s_util.get_helm_install_command(
        "csi-driver-nfs",
        "csi-driver-nfs",
        repository="https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts",
        chart_version="v4.7.0",
        images=images,
    )


def test_nfsplugin_integration(function_instance: harness.Instance):
    function_instance.exec(_get_nfsplugin_csi_helm_cmd("4.7.0"))

    k8s_util.wait_for_daemonset(function_instance, "csi-nfs-node", "kube-system")
    k8s_util.wait_for_deployment(function_instance, "csi-nfs-controller", "kube-system")
