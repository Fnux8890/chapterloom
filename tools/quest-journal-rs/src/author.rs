use crate::{
    pack::{files, output_parent, read},
    validate::{id, namespace},
};
use anyhow::{Context, Result, ensure};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{fs, path::Path};

fn write(path: &Path, text: &str) -> Result<()> {
    fs::create_dir_all(path.parent().context("invalid filename")?)?;
    fs::write(path, text)?;
    Ok(())
}
fn save(path: &Path, value: Value) -> Result<()> {
    write(path, &(serde_json::to_string_pretty(&value)? + "\n"))
}
fn publish_dir(
    output: &Path,
    source: Option<&Path>,
    populate: impl FnOnce(&Path) -> Result<()>,
) -> Result<()> {
    let tmp = tempfile::tempdir_in(output_parent(output, source)?)?;
    let stage = tmp.path().join("pack");
    fs::create_dir(&stage)?;
    populate(&stage)?;
    ensure!(!output.try_exists()?, "{} already exists", output.display());
    fs::rename(stage, output)?;
    Ok(())
}
pub fn init(folder: &Path, ns: &str, title: &str) -> Result<()> {
    ensure!(namespace(ns), "invalid namespace");
    ensure!(!title.trim().is_empty(), "supply a chapter title");
    publish_dir(folder, None, |base| {
        let data = base.join("data").join(ns);
        save(
            &base.join("pack.mcmeta"),
            json!({"pack":{"min_format":121,"max_format":121,"description":title}}),
        )?;
        save(
            &data.join("quest_chapter/journal.json"),
            json!({"version":1,"root":format!("{ns}:root"),"order":30}),
        )?;
        for (name, label, icon, hint, criterion, xp) in [
            (
                "root",
                title,
                "book",
                "Gather iron and complete your first job.",
                json!({"trigger":"minecraft:tick"}),
                0,
            ),
            (
                "iron_supply",
                "Source Iron",
                "iron_ingot",
                "Obtain iron. Reward: 5 XP.",
                json!({"trigger":"minecraft:inventory_changed","conditions":{"items":[{"items":"minecraft:iron_ingot"}]}}),
                5,
            ),
            (
                "first_job",
                "First Job",
                "anvil",
                "Complete a job in the host mod. Reward: 1 XP.",
                json!({"trigger":"minecraft:impossible"}),
                1,
            ),
        ] {
            let mut q = json!({"display":{"icon":{"id":format!("minecraft:{icon}")},"title":{"text":label},"description":{"text":hint},"show_toast":name!="root","announce_to_chat":false},"criteria":{"done":criterion}});
            if xp > 0 {
                q["parent"] = json!(format!("{ns}:root"));
                q["rewards"] = json!({"experience":xp});
            }
            save(&data.join(format!("advancement/{name}.json")), q)?;
        }
        save(
            &data.join("tags/function/api/v1/job_completed.json"),
            json!({"values":[format!("{ns}:journal/first_job")]}),
        )?;
        write(
            &data.join("function/journal/first_job.mcfunction"),
            &format!("advancement grant @s only {ns}:first_job\n"),
        )
    })
}
fn claim(base: &Path, rid: &str) -> Result<()> {
    let (ns, path) = id(rid)?;
    let data = base.join("data").join(ns);
    let adv = data.join("advancement");
    let src = adv.join(format!("{path}.json"));
    let mut quest = read(&src)?;
    let title = quest["display"]
        .get("title")
        .context("expected a displayed quest")?
        .clone();
    ensure!(
        title.get("horizon:claim_v1").is_none(),
        "{rid} already manual"
    );
    let rewards = quest["rewards"].clone();
    ensure!(
        rewards.as_object().is_some_and(|o| !o.is_empty()),
        "{rid} has no rewards to defer"
    );
    let helper = format!("journal_claim/{path}");
    let prefix = format!("{ns}:{helper}");
    let functions = data.join("function").join(&helper);
    ensure!(
        !functions.exists() && !adv.join(&helper).exists(),
        "reserved claim helper paths exist"
    );
    let digest = format!("{:x}", Sha256::digest(rid.as_bytes()));
    let objective = format!("qj{}", &digest[..14]);
    quest["display"]["title"] = json!({"text":"","extra":[title],"horizon:claim_v1":objective});
    quest["rewards"] = json!({"function":format!("{prefix}/earn")});
    save(&src, quest)?;
    let mut receipt = json!({"criteria":{"done":{"trigger":"minecraft:impossible"}}});
    save(&adv.join(&helper).join("earned.json"), receipt.clone())?;
    receipt["rewards"] = rewards;
    save(&adv.join(&helper).join("receipt.json"), receipt)?;
    let eligible =
        format!("advancements={{{rid}=true,{prefix}/earned=true,{prefix}/receipt=false}}");
    for (name, body) in [
        (
            "load",
            format!("scoreboard objectives add {objective} trigger"),
        ),
        (
            "earn",
            format!(
                "advancement grant @s only {prefix}/earned\nscoreboard players enable @s {objective}"
            ),
        ),
        (
            "tick",
            format!(
                "execute as @a[scores={{{objective}=1..}}] at @s run function {prefix}/collect\nscoreboard players enable @a[{eligible}] {objective}"
            ),
        ),
        (
            "collect",
            format!(
                "scoreboard players reset @s {objective}\nexecute if entity @s[{eligible}] run advancement grant @s only {prefix}/receipt"
            ),
        ),
    ] {
        write(
            &functions.join(format!("{name}.mcfunction")),
            &(body + "\n"),
        )?;
    }
    for name in ["load", "tick"] {
        let path = base.join(format!("data/minecraft/tags/function/{name}.json"));
        let mut tag = if path.exists() {
            read(&path)?
        } else {
            json!({"values":[]})
        };
        tag["values"]
            .as_array_mut()
            .context("expected function tag values array")?
            .push(json!(format!("{prefix}/{name}")));
        save(&path, tag)?;
    }
    Ok(())
}
pub fn manual(source: &Path, output: &Path, quests: &[String]) -> Result<()> {
    publish_dir(output, Some(source), |base| {
        for file in files(source)? {
            let dest = base.join(file.strip_prefix(source)?);
            fs::create_dir_all(dest.parent().unwrap())?;
            fs::copy(file, dest)?;
        }
        for rid in quests {
            claim(base, rid).with_context(|| format!("compiling {rid}"))?;
        }
        Ok(())
    })
}
