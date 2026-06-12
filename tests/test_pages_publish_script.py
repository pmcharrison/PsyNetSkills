import subprocess
from pathlib import Path


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def configure_user(repo: Path) -> None:
    git("config", "user.name", "Test User", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)


def test_push_pages_branch_rebases_changes_onto_latest_remote(tmp_path: Path) -> None:
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    stale_preview = tmp_path / "stale-preview"
    concurrent = tmp_path / "concurrent"
    final = tmp_path / "final"

    git("init", "--bare", str(origin), cwd=tmp_path)

    git("clone", str(origin), str(seed), cwd=tmp_path)
    configure_user(seed)
    write(seed / "index.html", "production v1\n")
    write(seed / "pr-preview/pr-1/index.html", "preview 1\n")
    git("add", "-A", cwd=seed)
    git("commit", "-m", "Initial pages", cwd=seed)
    git("push", "origin", "HEAD:gh-pages", cwd=seed)

    git("clone", str(origin), str(stale_preview), cwd=tmp_path)
    configure_user(stale_preview)
    git("checkout", "gh-pages", cwd=stale_preview)
    write(stale_preview / "pr-preview/pr-2/index.html", "preview 2\n")
    git("add", "-A", cwd=stale_preview)
    git("commit", "-m", "Deploy dashboard preview for PR #2", cwd=stale_preview)

    git("clone", str(origin), str(concurrent), cwd=tmp_path)
    configure_user(concurrent)
    git("checkout", "gh-pages", cwd=concurrent)
    write(concurrent / "index.html", "production v2\n")
    git("add", "-A", cwd=concurrent)
    git("commit", "-m", "Deploy production dashboard", cwd=concurrent)
    git("push", "origin", "HEAD:gh-pages", cwd=concurrent)

    script = Path(__file__).resolve().parents[1] / ".github/scripts/push-pages-branch.sh"
    subprocess.run(
        [str(script), str(stale_preview), "gh-pages"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    git("clone", "--branch", "gh-pages", str(origin), str(final), cwd=tmp_path)

    assert (final / "index.html").read_text(encoding="utf-8") == "production v2\n"
    assert (
        final / "pr-preview/pr-2/index.html"
    ).read_text(encoding="utf-8") == "preview 2\n"
    assert len(git("rev-list", "--parents", "-n", "1", "HEAD", cwd=final).split()) == 1


def test_prepare_production_pages_preserves_previews_and_artifacts(
    tmp_path: Path,
) -> None:
    pages_dir = tmp_path / "pages"
    write(pages_dir / "index.html", "old production\n")
    write(pages_dir / "css/site.css", "old css\n")
    write(pages_dir / "pr-preview/pr-182/index.html", "preview\n")
    write(
        pages_dir / "artifacts/blobs/sha256/ab/abcdef.mp4",
        "shared artifact\n",
    )

    script = (
        Path(__file__).resolve().parents[1]
        / ".github/scripts/prepare-production-pages.py"
    )
    subprocess.run(
        ["python", str(script), str(pages_dir)],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    assert not (pages_dir / "index.html").exists()
    assert not (pages_dir / "css").exists()
    assert (pages_dir / "pr-preview/pr-182/index.html").read_text(
        encoding="utf-8",
    ) == "preview\n"
    assert (pages_dir / "artifacts/blobs/sha256/ab/abcdef.mp4").read_text(
        encoding="utf-8",
    ) == "shared artifact\n"


def test_prepare_preview_pages_merges_shared_artifacts_without_preview_copies(
    tmp_path: Path,
) -> None:
    pages_dir = tmp_path / "pages"
    public_dir = tmp_path / "public"
    shared_large_reference = "x" * (600 * 1024)
    write(pages_dir / "pr-preview/pr-182/stale.html", "old preview\n")
    write(pages_dir / "pr-preview/pr-181/index.html", "other preview\n")
    write(
        pages_dir / "challenges/example/references/shared.zip",
        shared_large_reference,
    )
    write(
        pages_dir / "challenges/example/references/changed.zip",
        "old" * (200 * 1024),
    )
    write(
        pages_dir / "artifacts/blobs/sha256/ab/abcdef.mp4",
        "existing shared artifact\n",
    )
    write(public_dir / "index.html", "new preview\n")
    write(public_dir / "css/site.css", "body {}\n")
    write(
        public_dir / "artifacts/blobs/sha256/cd/cdef01.mp4",
        "new shared artifact\n",
    )
    write(public_dir / "artifacts/monitor-static/player.js", "player\n")
    write(
        public_dir / "challenges/example/references/shared.zip",
        shared_large_reference,
    )
    write(
        public_dir / "challenges/example/references/changed.zip",
        "new" * (200 * 1024),
    )
    write(
        public_dir / "challenges/example/references/small.txt",
        "small duplicate\n",
    )
    write(
        pages_dir / "challenges/example/references/small.txt",
        "small duplicate\n",
    )

    script = (
        Path(__file__).resolve().parents[1]
        / ".github/scripts/prepare-preview-pages.py"
    )
    subprocess.run(
        ["python", str(script), str(pages_dir), str(public_dir), "pr-preview/pr-182"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    assert not (pages_dir / "pr-preview/pr-182/stale.html").exists()
    assert (pages_dir / "pr-preview/pr-182/index.html").read_text(
        encoding="utf-8",
    ) == "new preview\n"
    assert (pages_dir / "pr-preview/pr-182/css/site.css").read_text(
        encoding="utf-8",
    ) == "body {}\n"
    assert not (pages_dir / "pr-preview/pr-182/artifacts").exists()
    assert not (
        pages_dir / "pr-preview/pr-182/challenges/example/references/shared.zip"
    ).exists()
    assert (
        pages_dir / "pr-preview/pr-182/challenges/example/references/changed.zip"
    ).read_text(encoding="utf-8") == "new" * (200 * 1024)
    assert (
        pages_dir / "pr-preview/pr-182/challenges/example/references/small.txt"
    ).read_text(encoding="utf-8") == "small duplicate\n"
    assert (pages_dir / "pr-preview/pr-181/index.html").read_text(
        encoding="utf-8",
    ) == "other preview\n"
    assert (pages_dir / "artifacts/blobs/sha256/ab/abcdef.mp4").read_text(
        encoding="utf-8",
    ) == "existing shared artifact\n"
    assert (pages_dir / "artifacts/blobs/sha256/cd/cdef01.mp4").read_text(
        encoding="utf-8",
    ) == "new shared artifact\n"
    assert (pages_dir / "artifacts/monitor-static/player.js").read_text(
        encoding="utf-8",
    ) == "player\n"
