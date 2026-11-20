"""Export a fresh world's datapacks and explicit low-to-high pack selection."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROFILES = json.loads((HERE/"profiles.json").read_text())


def export(profile, output):
    packs = PROFILES[profile]
    files = {}
    for pack in packs:
        base = HERE/pack if pack == "expert_rules" else ROOT/"datapacks"/pack
        if not (base/"pack.mcmeta").is_file():
            raise FileNotFoundError(base/"pack.mcmeta")
        for p in sorted(base.rglob("*")):
            if p.is_file():
                files[f"datapacks/{pack}/{p.relative_to(base).as_posix()}"] = p.read_bytes()
    selection = {"enabled":["vanilla", *["file/"+p for p in packs]], "disabled":[]}
    files["datapacks.json"] = json.dumps(selection, indent=2).encode()
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(ZipInfo(name), content, compress_type=ZIP_DEFLATED)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("profile", choices=PROFILES)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    export(args.profile, args.output)
