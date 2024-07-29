#
# Copyright 2024 Canonical, Ltd.
#

from k8s_test_harness.util import docker_util, env_util

ROCK_EXPECTED_FILES = [
    "/nfsplugin",
]


def test_csi_driver_nfs_rock():
    """Test NFS CSI driver rock."""

    rock = env_util.get_build_meta_info_for_rock_version("nfsplugin", "4.7.0", "amd64")
    image = rock.image

    # check rock filesystem.
    docker_util.ensure_image_contains_paths(image, ROCK_EXPECTED_FILES)

    # check binary.
    process = docker_util.run_in_docker(image, ["/nfsplugin", "--help"])
    assert "Usage of /nfsplugin:" in process.stderr
