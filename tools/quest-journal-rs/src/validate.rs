use crate::{
    Inputs,
    pack::{files, read},
};
use anyhow::{Context, Result, bail, ensure};
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    path::{Path, PathBuf},
};

pub fn namespace(s: &str) -> bool {
    !s.is_empty()
        && !s.starts_with('.')
        && s.bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b"_.-".contains(&b))
}
pub fn id(s: &str) -> Result<(&str, &str)> {
    let (ns, path) = s.split_once(':').context("expected namespaced ID")?;
    ensure!(
        namespace(ns)
            && path.split('/').all(|c| !c.is_empty()
                && c != "."
                && c != ".."
                && c.bytes()
                    .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b"_.-".contains(&b))),
        "invalid resource ID {s}"
    );
    Ok((ns, path))
}
fn format(v: &Value) -> Result<(i64, i64)> {
    if let Some(n) = v.as_i64() {
        return Ok((n, 0));
    }
    if let Some([a, b]) = v.as_array().map(Vec::as_slice)
        && let (Some(a), Some(b)) = (a.as_i64(), b.as_i64())
        && a >= 0
        && b >= 0
    {
        return Ok((a, b));
    }
    bail!("invalid pack format {v}")
}
type Entries = BTreeMap<String, Value>;
#[derive(Default)]
struct Registry {
    quests: Entries,
    chapters: Entries,
    rules: BTreeMap<String, PathBuf>,
}
impl Registry {
    fn load(&mut self, base: &Path) -> Result<()> {
        let meta = read(&base.join("pack.mcmeta"))?;
        let p = &meta["pack"];
        let bound = |key: &str| format(p.get(key).unwrap_or(&p["pack_format"]));
        ensure!(
            bound("min_format")? <= (121, 0) && bound("max_format")? >= (121, 0),
            "pack must support format 121"
        );
        let data = base.join("data");
        if !data.exists() {
            return Ok(());
        }
        for path in files(&data)? {
            if path.extension().and_then(|x| x.to_str()) != Some("json") {
                continue;
            }
            let rel = path
                .strip_prefix(&data)?
                .to_str()
                .context("invalid UTF-8 path")?
                .replace('\\', "/");
            let mut parts = rel.strip_suffix(".json").unwrap().splitn(3, '/');
            let (Some(ns), Some(kind), Some(name)) = (parts.next(), parts.next(), parts.next())
            else {
                continue;
            };
            if !matches!(kind, "advancement" | "quest_chapter" | "progression_rule") {
                continue;
            }
            let key = format!("{ns}:{name}");
            id(&key)?;
            match kind {
                "advancement" => {
                    self.quests.insert(key, read(&path)?);
                }
                "quest_chapter" => {
                    self.chapters.insert(key, read(&path)?);
                }
                _ => {
                    self.rules.insert(key, path);
                }
            }
        }
        Ok(())
    }
}
fn signed(v: &Value) -> bool {
    v.as_i64().is_some_and(|v| i16::try_from(v).is_ok())
}
fn graph(quests: &Entries) -> Result<BTreeMap<String, String>> {
    let mut roots = BTreeMap::new();
    for (rid, q) in quests {
        let criteria = q["criteria"].as_object().context("missing criteria")?;
        ensure!(!criteria.is_empty(), "empty criteria");
        for entry in criteria.values() {
            id(entry["trigger"].as_str().context("missing trigger")?)?;
        }
        if let Some(req) = q.get("requirements") {
            let mut used = BTreeSet::new();
            for group in req.as_array().context("expected requirements array")? {
                let group = group.as_array().context("expected requirement group")?;
                ensure!(!group.is_empty(), "empty requirement group");
                for key in group {
                    let key = key.as_str().context("invalid criterion")?;
                    ensure!(
                        criteria.contains_key(key),
                        "unknown required criterion {key}"
                    );
                    used.insert(key);
                }
            }
            ensure!(
                used.len() == criteria.len(),
                "requirements omit a criterion"
            );
        }
        let mut chain = BTreeSet::new();
        let mut node = rid.as_str();
        let root = loop {
            if let Some(root) = roots.get(node) {
                break String::clone(root);
            }
            ensure!(chain.insert(node), "parent cycle at {node}");
            let quest = quests
                .get(node)
                .with_context(|| format!("unresolved parent {node}"))?;
            let Some(parent) = quest.get("parent") else {
                break node.to_owned();
            };
            node = parent.as_str().context("invalid parent")?;
        };
        for node in chain {
            roots.insert(node.to_owned(), root.clone());
        }
    }
    Ok(roots)
}
fn chapter(
    reg: &Registry,
    roots: &BTreeMap<String, String>,
    claimed: &mut BTreeSet<String>,
    c: &Value,
) -> Result<()> {
    ensure!(
        c.as_object()
            .unwrap()
            .keys()
            .all(|k| matches!(k.as_str(), "version" | "root" | "positions" | "order")),
        "unknown chapter field"
    );
    ensure!(
        c["version"].as_i64() == Some(1) && c.get("order").is_none_or(signed),
        "invalid version or order"
    );
    let root = c["root"].as_str().context("missing root")?;
    let q = reg.quests.get(root).context("unresolved chapter root")?;
    ensure!(
        q.get("parent").is_none() && q["display"].get("title").is_some(),
        "expected displayed root {root}"
    );
    ensure!(claimed.insert(root.into()), "duplicate chapter root {root}");
    if let Some(pos) = c.get("positions") {
        for (rid, xy) in pos.as_object().context("expected positions object")? {
            ensure!(
                roots.get(rid).is_some_and(|r| r == root),
                "position outside chapter: {rid}"
            );
            ensure!(
                xy.as_array()
                    .is_some_and(|p| p.len() == 2 && p.iter().all(signed)),
                "invalid position {rid}"
            );
        }
    }
    Ok(())
}
fn rule(
    v: &Value,
    quests: &Entries,
    items: Option<&Value>,
    resources: Option<&Path>,
) -> Result<()> {
    ensure!(
        v.as_object().unwrap().len() == 5
            && v["version"].as_i64() == Some(1)
            && v["action"] == "craft"
            && v["scope"] == "player",
        "expected v1 player craft rule"
    );
    let output = v["output"].as_str().context("missing output")?;
    id(output)?;
    ensure!(
        items.is_none_or(|i| i.get(output).is_some()),
        "unknown output {output}"
    );
    ensure!(
        v["requires"].as_object().is_some_and(|c| c.len() == 1),
        "invalid requires"
    );
    let quest = v["requires"]["quest_completed"]
        .as_str()
        .context("missing quest_completed")?;
    let (ns, path) = id(quest)?;
    ensure!(
        quests.contains_key(quest)
            || resources.is_some_and(|r| r
                .join("data")
                .join(ns)
                .join("advancement")
                .join(format!("{path}.json"))
                .is_file()),
        "unresolved quest {quest}"
    );
    if let Some(criteria) = quests.get(quest).and_then(|q| q["criteria"].as_object())
        && criteria.values().any(|c| {
            c["trigger"] == "minecraft:inventory_changed"
                && c["conditions"]["items"]
                    .as_array()
                    .is_some_and(|preds| preds.iter().any(|p| p["items"] == output))
        })
    {
        eprintln!(
            "warning: {quest} requires obtaining its gated output {output}; document another source"
        );
    }
    Ok(())
}
pub fn check(inputs: &Inputs) -> Result<(usize, usize)> {
    let mut reg = Registry::default();
    for base in inputs.dependency.iter().chain([&inputs.folder]) {
        reg.load(base).with_context(|| base.display().to_string())?;
    }
    ensure!(
        !reg.chapters.is_empty() || !reg.rules.is_empty(),
        "no journal chapters or progression rules"
    );
    let roots = graph(&reg.quests)?;
    let mut claimed = BTreeSet::new();
    for (name, c) in &reg.chapters {
        chapter(&reg, &roots, &mut claimed, c).with_context(|| name.clone())?;
    }
    let resources = inputs.resources.as_deref();
    let items = if reg.rules.is_empty() {
        None
    } else {
        resources.map(|r| read(&r.join("items.json"))).transpose()?
    };
    for path in reg.rules.values() {
        rule(&read(path)?, &reg.quests, items.as_ref(), resources)
            .with_context(|| path.display().to_string())?;
    }
    Ok((reg.chapters.len(), reg.quests.len()))
}
