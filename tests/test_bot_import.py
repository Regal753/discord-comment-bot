from __future__ import annotations

import importlib
import unittest


class BotImportTests(unittest.TestCase):
    def test_import_has_no_runtime_login_side_effect(self) -> None:
        module = importlib.import_module("discord_comment_bot")
        self.assertIsNone(module.client_ai)


if __name__ == "__main__":
    unittest.main()
