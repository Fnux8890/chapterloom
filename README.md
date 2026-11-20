# Horizon Quest Journal

A quest book for Horizon 26.3. Press **L** to open a chapter, follow its quest map, and select a quest to see its objective and reward. Mods can contribute chapters and progression events. Modpacks can change rewards and decide which quests unlock crafting recipes.

![The Founders quest map beside the Set Up Camp objective and its Claim reward button](https://raw.githubusercontent.com/Fnux8890/horizon-quest-journal/v1.1.2-beta.1/docs/media/quest-journal/equal-page-spread.png)

## Play the public beta

1. Build the matching Horizon runtime using the [beta installation guide](https://github.com/Fnux8890/horizon-quest-journal/tree/v1.1.2-beta.1#build-the-beta-runtime). Single-player runs locally. Multiplayer requires the patched build on the host and each client.
2. Download the Founders chapter ZIP from the [public beta release](https://github.com/Fnux8890/horizon-quest-journal/releases/tag/v1.1.2-beta.1) and enable it in a fresh world's data packs.
3. Obtain a crafting table, open the journal, select **Set Up Camp**, and click **Claim reward** to collect 10 XP.

The release also includes two example world profiles. Beginner allows ordinary blast furnace crafting. Expert unlocks that recipe when the player completes **Set Up Camp**, even if they wait to claim the XP.

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

## Optional author tools

The [Rust CLI](https://github.com/Fnux8890/horizon-quest-journal/tree/4509be508d2a5325782e5f7be0fb525abedc088a/tools/quest-journal-rs) and [Python CLI](https://github.com/Fnux8890/horizon-quest-journal/tree/4509be508d2a5325782e5f7be0fb525abedc088a/tools/quest-journal) both support `init`, `check`, `manual`, and `build`. Choose either for the same data pack. Players only need the pack and the matching journal runtime.

Install the standalone Rust CLI with Cargo:

```sh
cargo install --locked --git https://github.com/Fnux8890/horizon-quest-journal --rev 4509be508d2a5325782e5f7be0fb525abedc088a quest-journal
quest-journal check camp_rules --dependency datapacks/horizon_quests
```

With Python 3.10+, run `python tools/quest-journal/journal.py check camp_rules --dependency datapacks/horizon_quests` from the source checkout. In both examples, point the input and dependency paths at your unpacked packs.

[Mod author guide](https://github.com/Fnux8890/horizon-quest-journal/blob/4509be508d2a5325782e5f7be0fb525abedc088a/tools/quest-journal/README.md) · [Modpack guide](https://github.com/Fnux8890/horizon-quest-journal/blob/4509be508d2a5325782e5f7be0fb525abedc088a/docs/quest-gated-crafting.md) · [Beta source and contribution instructions](https://github.com/Fnux8890/horizon-quest-journal/tree/v1.1.2-beta.1#contribute)
