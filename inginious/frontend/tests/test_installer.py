# pylint: disable=redefined-outer-name
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import docker
import pytest

from inginious.frontend.installer import Installer


class TestInstaller(object):

    def test_installer_init(self):
        inst = Installer()
        assert inst is not None

    def test_configuration_filename(self):
        inst = Installer()
        assert inst.configuration_filename() == "configuration.yaml"

    def test_local_docker_conf(self):
        inst = Installer()
        try:
            t = docker.from_env().version()['ApiVersion']
        except:
            assert False
        assert inst.test_local_docker_conf()

