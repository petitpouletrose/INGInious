# pylint: disable=redefined-outer-name
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import gettext

import pytest

from inginious.frontend.l10n_manager import L10nManager


class TestInstaller(object):

    def test_installer_init(self):
        inst = L10nManager()
        assert inst is not None

    def test_get_translation_obj(self):
        inst = L10nManager()
        translation_object = inst.get_translation_obj()
        assert translation_object is not None
        lang = "fr"
        translation_object = inst.get_translation_obj(lang)
        assert translation_object is not None
        lang="test"
        translation_object = inst.get_translation_obj(lang)
        assert isinstance(translation_object, gettext.NullTranslations)

    def test_gettext(self):
        inst = L10nManager()
        get_text = inst.gettext("test")
        assert get_text is not None


