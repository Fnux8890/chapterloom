"""Compare both author tools against the same pack. Pass the built Rust executable."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

SDK = Path(__file__).resolve().parents[1] / "quest-journal"
RUST = [str(Path(sys.argv[1]).resolve())]
PYTHON = [sys.executable, str(SDK / "journal.py")]


def run(tool, *args, ok=True):
    process = subprocess.run([*tool, *map(str, args)], capture_output=True, text=True)
    assert (process.returncode == 0) == ok, (args, process.stdout, process.stderr)


def pack_contents(folder):
    result = {}
    for entry in folder.rglob("*"):
        if entry.is_file():
            key = entry.relative_to(folder).as_posix()
            result[key] = (json.loads(entry.read_bytes()) if entry.suffix in (".json", ".mcmeta")
                           else entry.read_text(encoding="utf8"))
    return result


def archive_contents(path):
    with ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


with TemporaryDirectory() as temp:
    root = Path(temp)
    chapter = root / "python"
    starter = root / "rust"
    for tool, dest in [(PYTHON, chapter), (RUST, starter)]:
        run(tool, "init", dest, "--namespace", "survey", "--title", "Survey")
        run(tool, "init", dest, "--namespace", "survey", "--title", "Survey", ok=False)
    assert pack_contents(chapter) == pack_contents(starter)

    # Include existing tags and non-XP rewards when comparing claim receipts.
    src = chapter / "data/survey/advancement/first_job.json"
    quest = json.loads(src.read_bytes())
    quest["rewards"] = {"experience": 10, "loot": ["survey:bricks"], "function": "survey:celebrate"}
    src.write_text(json.dumps(quest), encoding="utf8")
    load = chapter / "data/minecraft/tags/function/load.json"
    load.parent.mkdir(parents=True)
    load.write_text('{"values":["survey:existing"]}', encoding="utf8")
    for tool, name in [(RUST, "rust-claims"), (PYTHON, "python-claims")]:
        run(tool, "manual", chapter, root / name, "--quest", "survey:first_job",
            "--quest", "survey:iron_supply")
        run(tool, "check", root / name)
        run(tool, "manual", chapter, root / "failed", "--quest", "survey:first_job",
            "--quest", "survey:first_job", ok=False)
        assert not (root / "failed").exists()
    assert pack_contents(root / "rust-claims") == pack_contents(root / "python-claims")

    rules = root / "camp"
    rule = rules / "data/camp/progression_rule/gate.json"
    rule.parent.mkdir(parents=True)
    (rules / "pack.mcmeta").write_bytes((chapter / "pack.mcmeta").read_bytes())
    gate = {"version": 1, "action": "craft", "scope": "player", "output": "minecraft:furnace",
            "requires": {"quest_completed": "survey:first_job"}}
    rule.write_text(json.dumps(gate))
    resources = root / "resources"
    resources.mkdir()
    (resources / "items.json").write_text('{"minecraft:furnace":{}}')
    flags = ["--dependency", chapter, "--resources", resources]
    for tool, name in [(RUST, "rust"), (PYTHON, "python")]:
        run(tool, "check", rules, ok=False)
        run(tool, "build", rules, root / (name + ".zip"), *flags)
        run(tool, "build", rules, root / (name + ".zip"), *flags, ok=False)
    assert archive_contents(root / "rust.zip") == archive_contents(root / "python.zip")
    run(RUST, "build", rules, root / "repeat.zip", *flags)
    assert (root / "rust.zip").read_bytes() == (root / "repeat.zip").read_bytes()
    for invalid in [json.dumps({**gate, "output": "test:missing"}), '{"key":1,"key":2}']:
        rule.write_text(invalid)
        for tool in (RUST, PYTHON):
            run(tool, "build", rules, root / "invalid.zip", *flags, ok=False)
            assert not (root / "invalid.zip").exists()

    # Invalid quest graphs and chapter manifests must agree as well.
    for change in [{"parent": "survey:first_job"}, {"parent": "other:missing"},
                   {"requirements": [["unknown"]]}, {"criteria": {}}]:
        src.write_text(json.dumps({**quest, **change}))
        for tool in (RUST, PYTHON):
            run(tool, "check", chapter, ok=False)
    src.write_text(json.dumps(quest))
    manifest = chapter / "data/survey/quest_chapter/journal.json"
    original = json.loads(manifest.read_bytes())
    for change in [{"positions": {"survey:missing": [0, 0]}}, {"order": 32768},
                   {"root": "survey:first_job"}, {"version": True}]:
        manifest.write_text(json.dumps({**original, **change}))
        for tool in (RUST, PYTHON):
            run(tool, "check", chapter, ok=False)

print("Both CLIs passed starter, claims, dependency, item registry and archive fixtures.")
