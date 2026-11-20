# Horizon Quest Journal

**Public beta 1.1.2-beta.1 Â· Horizon 26.3.** Press **L** to open a hardcover journal, follow the branches of a chapter and select a quest to read its objective and rewards. Obtain a crafting table in the Founders chapter to complete **Set Up Camp**, select its gold exclamation mark and choose **Claim reward** for 10 XP.

![Open quest journal with chapter map and quest details](docs/media/quest-journal/equal-page-spread.png)

[Download the Founders pack and example profiles](https://github.com/Fnux8890/horizon-quest-journal/releases/tag/v1.1.2-beta.1)

## Build the beta runtime

The book, claim button and player crafting rules require a patched Horizon executable. The downloadable Founders ZIP supplies world data. For solo play, build the client and open a local world. For multiplayer, use matching patched builds on the clients and the host. This beta distributes source and world data. Bring your own Horizon-compatible Minecraft 26.3 resources.

From a checkout of this beta, with Git, the Horizon build prerequisites and Rust installed, run:

```sh
git clone https://github.com/horizon-rust/horizon.git engine
git -C engine checkout --detach 7bf49fa2810efa4e293e8867cabe831fea59378d
git -C engine apply --check ../patches/quest-map.patch
git -C engine apply ../patches/quest-map.patch
cargo build --manifest-path engine/Cargo.toml --locked --profile fast -p horizon-client --bin horizon-client
```

Start the built executable under `engine/target/fast/` with your normal Horizon game directory and extracted resources. Use a fresh beta world. Place the Founders ZIP in that world's `datapacks/` directory and reopen the world. An operator can run `/reload`, inspect `/datapack list`, and use `/datapack enable "file/<filename>.zip"` if the pack is available but disabled. In single-player you can also select the pack at world creation. The registry entry installs this chapter. On the ordinary engine, the advancement data can load, but the book and its claim interface require the patched runtime.

## Gate a recipe with a data pack

In a fresh world with the beta runtime and Founders chapter enabled, create a folder named `camp_rules` inside the world's `datapacks/` folder. Add these two files with a text editor.

**`camp_rules/pack.mcmeta`**

```json
{"pack":{"description":"Camp crafting rules","min_format":121,"max_format":121}}
```

**`camp_rules/data/camp/progression_rule/blast_furnace.json`**

```json
{
  "version": 1,
  "action": "craft",
  "scope": "player",
  "output": "minecraft:blast_furnace",
  "requires": {"quest_completed": "horizon:workbench"}
}
```

Run `/reload` and check `/datapack list enabled`. If needed, run `/datapack enable "file/camp_rules" last`. To test, use a player who has never obtained a crafting table and open one already placed in the world. Assemble a blast furnace: the result shows a red barrier. Pick up a crafting table to complete **Set Up Camp**, then try the recipe again. You can craft the furnace before claiming the XP.

## Add quests to a mod

Ship a companion data pack with your mod. Put the chapter definition under `data/<namespace>/quest_chapter/` and its quests under `data/<namespace>/advancement/`. Use a built-in advancement trigger for actions such as obtaining an item. For a custom action, have the mod call a namespaced function tag as the credited player after the action succeeds.

See the [mod author guide](tools/quest-journal/README.md) for chapter files, callbacks and claimable rewards. The [modpack guide](docs/quest-gated-crafting.md) covers pack priority and overrides.

Choose the [Rust CLI](tools/quest-journal-rs/README.md) or the [Python CLI](tools/quest-journal/README.md#optional-cli-for-scaffolding-validation-and-packaging) to scaffold a chapter, check references across packs, create claimable rewards, or build a ZIP. The game reads the same JSON files from a folder or a ZIP.

![Locked blast furnace in the Expert profile](docs/media/quest-journal/stock-blast-furnace-locked.png)

## Contribute

Run `python tools/quest-journal/test_journal.py` before opening a PR. For a gameplay change, include the engine revision, profile, solo or multiplayer steps and expected result. For UI changes, include an in-game screenshot. The original source and pack definitions use the [MIT license](LICENSE). The engine patch includes Horizon code under its [original MIT notice](tools/quest-journal/HORIZON-LICENSE.txt). See [provenance](tools/quest-journal/PROVENANCE.md).
