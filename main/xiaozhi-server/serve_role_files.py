import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


PUBLIC_CACHE = "public, max-age=31536000, immutable"
FILE_SETS = {
    "public-assets": {
        "/pet_expert_shilang-2026.08.16.2.bin": (
            Path("/roles/pet_expert_shilang-2026.08.16.2.bin"),
            "application/octet-stream",
            PUBLIC_CACHE,
        ),
        "/cheese_cat-2026.08.16.2.bin": (
            Path("/roles/cheese_cat-2026.08.16.2.bin"),
            "application/octet-stream",
            PUBLIC_CACHE,
        ),
        "/beta_dog-2026.08.16.2.bin": (
            Path("/roles/beta_dog-2026.08.16.2.bin"),
            "application/octet-stream",
            PUBLIC_CACHE,
        ),
        "/pet_expert_shilang-2026.08.16.1.bin": (
            Path("/roles/pet_expert_shilang-2026.08.16.1.bin"),
            "application/octet-stream",
            PUBLIC_CACHE,
        ),
        "/cheese_cat-2026.08.16.1.bin": (
            Path("/roles/cheese_cat-2026.08.16.1.bin"),
            "application/octet-stream",
            PUBLIC_CACHE,
        ),
        "/beta_dog-2026.08.16.1.bin": (
            Path("/roles/beta_dog-2026.08.16.1.bin"),
            "application/octet-stream",
            PUBLIC_CACHE,
        ),
    },
    "public-avatars": {
        "/pet_expert_shilang_idle.png": (
            Path("/avatars/pet_expert_shilang_idle.png"),
            "image/png",
            PUBLIC_CACHE,
        ),
        "/cheese_cat_idle.png": (
            Path("/avatars/cheese_cat_idle.png"),
            "image/png",
            PUBLIC_CACHE,
        ),
        "/beta_dog_idle.png": (
            Path("/avatars/beta_dog_idle.png"),
            "image/png",
            PUBLIC_CACHE,
        ),
    },
    "internal": {
        "/nezuko_proto-2026.08.16.2.bin": (
            Path("/roles/nezuko_proto-2026.08.16.2.bin"),
            "application/octet-stream",
            "no-store",
        ),
        "/nezuko_proto-2026.08.16.1.bin": (
            Path("/roles/nezuko_proto-2026.08.16.1.bin"),
            "application/octet-stream",
            "no-store",
        ),
        "/nezuko_proto_idle_round_v2.png": (
            Path("/avatars/nezuko_proto_idle_round_v2.png"),
            "image/png",
            "no-store",
        ),
    },
}


def configured_files() -> dict[str, tuple[Path, str, str]]:
    file_set = os.environ.get("ROLE_FILE_SET", "")
    try:
        return FILE_SETS[file_set]
    except KeyError as exc:
        raise SystemExit(f"Unknown ROLE_FILE_SET: {file_set!r}") from exc


FILES = configured_files()


class ExactFileHandler(SimpleHTTPRequestHandler):
    def _serve(self, include_body: bool) -> None:
        entry = FILES.get(urlsplit(self.path).path)
        if entry is None:
            self.send_error(404)
            return

        path, content_type, cache_control = entry
        try:
            size = path.stat().st_size
            stream = path.open("rb")
        except OSError:
            self.send_error(404)
            return

        with stream:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", cache_control)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if include_body:
                self.copyfile(stream, self.wfile)

    def do_GET(self) -> None:
        self._serve(include_body=True)

    def do_HEAD(self) -> None:
        self._serve(include_body=False)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), ExactFileHandler).serve_forever()
