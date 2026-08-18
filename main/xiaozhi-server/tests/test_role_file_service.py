import importlib.util
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "serve_role_files.py"


def load_service(file_set: str):
    spec = importlib.util.spec_from_file_location(
        f"serve_role_files_{file_set}", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, {"ROLE_FILE_SET": file_set}):
        spec.loader.exec_module(module)
    return module


class RoleFileServiceTest(TestCase):
    def test_public_asset_set_is_an_exact_allowlist(self):
        module = load_service("public-assets")

        self.assertEqual(
            set(module.FILES),
            {
                "/pet_expert_shilang-2026.08.18.5.bin",
                "/pet_expert_shilang-2026.08.18.4.bin",
                "/pet_expert_shilang-2026.08.18.3.bin",
                "/pet_expert_shilang-2026.08.18.2.bin",
                "/pet_expert_shilang-2026.08.18.1.bin",
                "/pet_expert_shilang-2026.08.17.1.bin",
                "/cheese_cat-2026.08.17.1.bin",
                "/beta_dog-2026.08.17.1.bin",
                "/pet_expert_shilang-2026.08.16.2.bin",
                "/cheese_cat-2026.08.16.2.bin",
                "/beta_dog-2026.08.16.2.bin",
                "/pet_expert_shilang-2026.08.16.1.bin",
                "/cheese_cat-2026.08.16.1.bin",
                "/beta_dog-2026.08.16.1.bin",
            },
        )
        self.assertNotIn("/oversize-5m.bin", module.FILES)
        self.assertNotIn("/catalog.json", module.FILES)

    def test_public_avatar_set_excludes_superseded_characters(self):
        module = load_service("public-avatars")

        self.assertEqual(
            set(module.FILES),
            {
                "/pet_expert_shilang_idle-2026.08.18.5.png",
                "/pet_expert_shilang_idle-2026.08.18.3.png",
                "/pet_expert_shilang_idle-2026.08.18.1.png",
                "/pet_expert_shilang_idle.png",
                "/cheese_cat_idle.png",
                "/beta_dog_idle.png",
            },
        )
        self.assertNotIn("/tech_cat_idle.png", module.FILES)

    def test_internal_set_only_contains_nezuko_prototype(self):
        module = load_service("internal")

        self.assertEqual(
            set(module.FILES),
            {
                "/nezuko_proto-2026.08.17.1.bin",
                "/nezuko_proto-2026.08.16.2.bin",
                "/nezuko_proto-2026.08.16.1.bin",
                "/nezuko_proto_idle_round_v2.png",
            },
        )

    def test_unknown_file_set_fails_closed(self):
        with self.assertRaises(SystemExit):
            load_service("unknown")
