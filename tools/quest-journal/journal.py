"""Build Chapterloom v1 companion packs. Python 3.10+, standard library."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

NS = re.compile(r"[a-z0-9_-][a-z0-9_.-]*")
PATH = re.compile(r"[a-z0-9_.-]+(?:/[a-z0-9_.-]+)*")


def resource(value):
    if not isinstance(value, str) or value.count(":") != 1:
        return False
    namespace, path = value.split(":")
    return NS.fullmatch(namespace) and PATH.fullmatch(path) and all(
        part not in (".", "..") for part in path.split("/")
    )


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field {key!r}")
        result[key] = value
    return result


def read(path):
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=object_pairs)
        if not isinstance(obj, dict):
            raise ValueError("expected a JSON object")
        return obj
    except ValueError as err:
        raise ValueError(f"{path}: {err}") from err


def check(condition, message):
    if not condition:
        raise ValueError(message)


def write(base, relative, value):
    path = base / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def init(folder, ns, title):
    check(NS.fullmatch(ns), "invalid namespace")
    check(title.strip(), "supply a chapter title")
    check(not folder.exists(), f"{folder} already exists")
    folder.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=folder.parent) as temporary:
        base = Path(temporary) / "pack"
        data = Path("data") / ns
        write(base, "pack.mcmeta", {"pack": {"min_format": 121, "max_format": 121, "description": title}})
        write(base, data/"quest_chapter/journal.json", {"version": 1, "root": ns+":root", "order": 30})
        for name, label, icon, hint, criterion in (
            ("root", title, "book", "Gather iron and complete your first job.", {"trigger":"minecraft:tick"}),
            ("iron_supply", "Source Iron", "iron_ingot", "Obtain iron. Reward: 5 XP.",
             {"trigger":"minecraft:inventory_changed", "conditions":{"items":[{"items":"minecraft:iron_ingot"}]}}),
            ("first_job", "First Job", "anvil", "Complete a job in the host mod. Reward: 1 XP.",
             {"trigger":"minecraft:impossible"}),
        ):
            quest = {"display":{"icon":{"id":"minecraft:"+icon}, "title":{"text":label},
                                "description":{"text":hint}, "show_toast":name != "root", "announce_to_chat":False},
                     "criteria":{"done":criterion}}
            if name != "root":
                quest.update(parent=ns+":root", rewards={"experience":5 if name == "iron_supply" else 1})
            write(base, data/f"advancement/{name}.json", quest)
        write(base, data/"tags/function/api/v1/job_completed.json", {"values":[ns+":journal/first_job"]})
        handler = base/data/"function/journal/first_job.mcfunction"
        handler.parent.mkdir(parents=True)
        handler.write_text(f"advancement grant @s only {ns}:first_job\n", encoding="utf8")
        validate([base])
        base.rename(folder)


def compile_claim(base, rid):
    check(resource(rid), f"invalid quest ID {rid!r}")
    ns, path = rid.split(":")
    data = Path("data")/ns
    source = data/"advancement"/(path+".json")
    quest = read(base/source)
    display = quest.get("display")
    check(isinstance(display, dict) and "title" in display, f"{rid}: expected a displayed quest")
    title = display["title"]
    check(not isinstance(title, dict) or "horizon:claim_v1" not in title, f"{rid}: already manual")
    rewards = quest.get("rewards")
    check(isinstance(rewards, dict) and rewards, f"{rid}: no rewards to defer")
    objective = "qj" + hashlib.sha256(rid.encode()).hexdigest()[:14]
    helper = f"journal_claim/{path}"
    prefix = f"{ns}:{helper}"
    check(not (base/data/"function"/helper).exists() and not (base/data/"advancement"/helper).exists(),
          f"{rid}: reserved helper paths already exist")
    display["title"] = {"text":"", "extra":[title], "horizon:claim_v1":objective}
    quest["rewards"] = {"function":prefix+"/earn"}
    write(base, source, quest)
    criterion = {"criteria":{"done":{"trigger":"minecraft:impossible"}}}
    write(base, data/"advancement"/helper/"earned.json", criterion)
    write(base, data/"advancement"/helper/"receipt.json", dict(criterion, rewards=rewards))
    eligible = f"@a[advancements={{{rid}=true,{prefix}/earned=true,{prefix}/receipt=false}}]"
    functions = {
        "load": [f"scoreboard objectives add {objective} trigger"],
        "earn": [f"advancement grant @s only {prefix}/earned", f"scoreboard players enable @s {objective}"],
        "tick": [f"execute as @a[scores={{{objective}=1..}}] at @s run function {prefix}/collect",
                 f"scoreboard players enable {eligible} {objective}"],
        "collect": [f"scoreboard players reset @s {objective}",
                    f"execute if entity @s[advancements={{{rid}=true,{prefix}/earned=true,{prefix}/receipt=false}}] run advancement grant @s only {prefix}/receipt"],
    }
    for name, lines in functions.items():
        target = base/data/"function"/helper/(name+".mcfunction")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines)+"\n", encoding="utf8")
    for name in ("load","tick"):
        target = Path("data/minecraft/tags/function")/(name+".json")
        tag = read(base/target) if (base/target).exists() else {"values":[]}
        check(isinstance(tag.get("values"), list), f"{target}: expected values array")
        tag["values"].append(prefix+"/"+name)
        write(base, target, tag)


def manual(source, output, quest_ids):
    check(not output.exists(), f"{output} already exists")
    check(not output.resolve().is_relative_to(source.resolve()), "choose an output outside the source pack")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        base = Path(temp)/"pack"
        shutil.copytree(source,base)
        for rid in quest_ids:
            compile_claim(base,rid)
        base.rename(output)


def signed(value):
    return type(value) is int and -32768 <= value <= 32767


def validate(packs, resources=None):
    quests, chapters, rules = {}, {}, {}
    for base in packs:  # Later packs override earlier resources, as in the game.
        meta = read(base/"pack.mcmeta").get("pack")
        check(isinstance(meta, dict), f"{base}: missing pack metadata")
        def format_pair(value):
            if type(value) is int:
                return (value, 0)
            if isinstance(value, list) and len(value) == 2 and all(type(v) is int and v >= 0 for v in value):
                return tuple(value)
            raise ValueError(f"{base}: invalid pack format {value!r}")
        low = format_pair(meta.get("min_format", meta.get("pack_format")))
        high = format_pair(meta.get("max_format", meta.get("pack_format")))
        check(low <= (121, 0) <= high, f"{base}: pack must support Horizon format 121")
        for kind, registry in (("advancement", quests), ("quest_chapter", chapters), ("progression_rule", rules)):
            for path in sorted((base/"data").glob(f"*/{kind}/**/*.json")):
                ns, _, *parts = path.relative_to(base/"data").parts
                rid = ns + ":" + Path(*parts).with_suffix("").as_posix()
                check(resource(rid), f"{path}: invalid resource ID {rid}")
                registry[rid] = path if kind == "progression_rule" else read(path)
    items = read(resources/"items.json") if rules and resources else None
    for rid, path in rules.items():
        rule = read(path)
        check(set(rule) == {"version", "action", "scope", "output", "requires"}, f"{path}: invalid rule fields")
        check(type(rule["version"]) is int and rule["version"] == 1 and
              rule["action"] == "craft" and rule["scope"] == "player", f"{path}: expected v1 player craft")
        check(resource(rule["output"]), f"{path}: invalid output ID")
        if items is not None:
            check(rule["output"] in items, f"{path}: unknown output {rule['output']}")
        cond = rule["requires"]
        check(isinstance(cond, dict) and set(cond) == {"quest_completed"}, f"{path}: invalid requires")
        quest = cond["quest_completed"]
        check(resource(quest), f"{path}: invalid quest ID")
        ns, name = quest.split(":")
        builtin = resources and (resources/"data"/ns/"advancement"/(name+".json")).is_file()
        check(quest in quests or builtin, f"{path}: unresolved quest {quest!r} (supply its dependency)")
        criteria = quests.get(quest, {}).get("criteria")
        if isinstance(criteria, dict):
            for criterion in criteria.values():
                if not isinstance(criterion, dict) or criterion.get("trigger") != "minecraft:inventory_changed":
                    continue
                conditions = criterion.get("conditions")
                predicates = conditions.get("items") if isinstance(conditions, dict) else None
                if isinstance(predicates, list) and any(
                    isinstance(item, dict) and item.get("items") == rule["output"] for item in predicates
                ):
                    print(f"warning: {rid} requires obtaining its gated output; document another source", file=sys.stderr)
                    break
    roots = {}
    for cid, c in chapters.items():
        check(set(c) <= {"version","root","order","positions"}, f"{cid}: unknown chapter field")
        check(type(c.get("version")) is int and c["version"] == 1, f"{cid}: expected version 1")
        check(signed(c.get("order",0)), f"{cid}: order must be a signed 16-bit integer")
        root = c.get("root")
        check(resource(root) and root in quests, f"{cid}: unresolved root {root!r} (supply its dependency)")
        q = quests[root]
        check("parent" not in q and isinstance(q.get("display"),dict) and "title" in q["display"],
              f"{cid}: {root} must be a displayed root")
        check(root not in roots, f"{cid}: {root} already claimed by {roots.get(root)}")
        roots[root] = cid
        positions = c.get("positions", {})
        check(isinstance(positions,dict), f"{cid}: positions must be an object")
        for rid, xy in positions.items():
            check(resource(rid) and isinstance(xy,list) and len(xy)==2 and all(map(signed,xy)),
                  f"{cid}: invalid position for {rid}")
    ends = {}
    for rid, q in quests.items():
        criteria = q.get("criteria")
        check(isinstance(criteria,dict) and criteria and all(isinstance(v,dict) and resource(v.get("trigger"))
              for v in criteria.values()), f"{rid}: invalid advancement criteria (use namespaced triggers)")
        if "requirements" in q:
            groups = q["requirements"]
            check(isinstance(groups, list) and groups and all(
                isinstance(group, list) and group and all(isinstance(key, str) and key in criteria for key in group)
                for group in groups), f"{rid}: requirements must reference declared criteria")
            check({key for group in groups for key in group} == set(criteria),
                  f"{rid}: requirements omit a criterion")
        chain = set()
        node = rid
        while node not in ends:
            check(node not in chain, f"{rid}: parent cycle at {node}")
            chain.add(node)
            parent = quests[node].get("parent")
            if "parent" not in quests[node]:
                ends[node] = node
                break
            check(resource(parent) and parent in quests, f"{node}: unresolved parent {parent!r} (supply its dependency)")
            node = parent
        ends.update(dict.fromkeys(chain, ends[node]))
    for root, cid in roots.items():
        for rid in chapters[cid].get("positions", {}):
            check(ends.get(rid) == root, f"{cid}: positioned node {rid} is outside its tree")
    check(chapters or rules, "no journal chapters or progression rules in the supplied packs")
    return len(chapters), len(quests)


def archive(base, destination, deps, resources=None):
    validate([*deps, base], resources)
    check(not destination.exists(), f"{destination} already exists")
    check(not destination.resolve().is_relative_to(base.resolve()), "choose an output outside the pack")
    files = [base/"pack.mcmeta"]
    if (base/"pack.png").is_file():
        files.append(base/"pack.png")
    files.extend(p for p in (base/"data").rglob("*") if p.is_file())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
        name = temp.name
    try:
        with ZipFile(name, "w") as z:
            for p in sorted(files):
                relative = p.relative_to(base)
                check(p.resolve().is_relative_to(base.resolve()), f"external file {relative}")
                z.writestr(ZipInfo(relative.as_posix()), p.read_bytes(), compress_type=ZIP_DEFLATED)
        # Exclusive publication also preserves a concurrent build's output.
        os.link(name, destination)
    finally:
        os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    starter = commands.add_parser("init", help="create an independent example mod companion")
    starter.add_argument("folder", type=Path)
    starter.add_argument("--namespace", required=True)
    starter.add_argument("--title", required=True)
    claims = commands.add_parser("manual", help="generate a pack with click-to-claim rewards")
    claims.add_argument("folder", type=Path)
    claims.add_argument("output", type=Path)
    claims.add_argument("--quest", action="append", required=True)
    for cmd in ("check","build"):
        sub = commands.add_parser(cmd)
        sub.add_argument("folder", type=Path)
        sub.add_argument("--dependency", type=Path, action="append", default=[], help="lower-priority unpacked data pack (repeatable)")
        sub.add_argument("--resources", type=Path, help="Horizon resource root containing items.json and data/")
        if cmd == "build":
            sub.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init(args.folder,args.namespace,args.title)
            print(f"Created {args.folder}")
        elif args.command == "manual":
            manual(args.folder,args.output,args.quest)
            print(f"Created manual-claim pack {args.output}")
        elif args.command == "check":
            ch, q = validate([*args.dependency,args.folder], args.resources)
            print(f"OK: {ch} chapter(s), {q} advancement(s)")
        else:
            archive(args.folder,args.output,args.dependency,args.resources)
            print(f"Built {args.output}")
    except (ValueError,OSError) as err:
        parser.exit(1, f"error: {err}\n")


if __name__ == "__main__":
    main()
