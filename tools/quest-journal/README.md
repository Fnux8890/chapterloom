# Horizon Quest Journal 1.1

A chapter is a data pack. A new mod can contribute quests, attach children to another mod's chapter, or award a quest after a server action succeeds. Players press **L**, use the arrows around the chapter counter, drag the map, and select an item to read its objective and reward. The Advancements button opens the standard advancement view.

## Start with a companion data pack

For a working example, copy the [Field Engineering pack](../../datapacks/engineering_press) into a fresh world's `datapacks/` folder. Enable it and open **L** on the beta runtime. Its `data/engineering/quest_chapter/field.json` file points to the chapter's root advancement, `engineering:press`. Edit the display description in `data/engineering/advancement/press.json`, run `/reload`, and reopen the chapter to see your change.

For your own mod, use your own namespace for the folder, root, parents, and function references. For a modpack override, keep the original namespace and file path and load the override pack last. The [two-file crafting example](../../README.md#gate-a-recipe-with-a-data-pack) walks through a rule you can test in-game.

## Optional CLI for scaffolding, validation and packaging

Use Python 3.10 or later. From the SDK directory run the following. The CLI works offline and uses the Python standard library.

~~~powershell
python journal.py init workshop --namespace workshop --title "Workshop Journal"
python journal.py check workshop
python journal.py build workshop workshop-1.0.zip
~~~

Place the ZIP in your single-player save's datapacks directory or the dedicated world's datapacks directory. Start the server or issue the following console commands on a running server. The exact pack ID includes the ZIP extension. Use the name shown by the list command if the file was renamed.

~~~text
reload
datapack list available
datapack enable "file/workshop-1.0.zip"
~~~

Open **L**. The starter awards **5 XP** for obtaining iron. Its second quest, **First Job**, awards **1 XP** when the host mod reports a completed job. Try this operator command in game twice and inspect the reward. The same advancement grant is idempotent while the player retains the advancement.

~~~text
/execute as @s at @s run function #workshop:api/v1/job_completed
~~~

Edit the generated files, check them again, and build to a fresh filename outside the source folder. For deployment, replace the contents of the original installed ZIP under the same filename, then reload. Preserve released namespace and advancement IDs to retain progress.

## Make a reward claimable

With the claim-aware journal runtime, each quest can pay on completion or wait for the player to collect. From the SDK folder, generate a new companion pack from your authoring folder. Repeat --quest to opt in additional IDs.

~~~powershell
python journal.py manual workshop workshop-manual --quest workshop:first_job
python journal.py check workshop-manual
python journal.py build workshop-manual workshop-manual.zip
~~~

Install the generated pack in place of its automatic version. Maintain the original quest ID and criteria. The quest completes immediately, so progression checks can use it before collection. Select the gold **!** node in the book and click **Claim reward**. The server pays the original reward bundle, including XP, loot tables, recipes and reward functions, then the book shows **Claimed**. Players who finished the earlier automatic version keep their payout.

The generated pack includes private earned and receipt advancement IDs under journal_claim, plus a namespaced function group and a trigger scoreboard objective. Preserve these IDs on upgrade. For a pack-specific payout, override the receipt advancement or rebuild from the editable source with the desired rewards. A reward function that contains gameplay progression effects will run at collection time. Put immediate progression at the objective's completion instead. Ordinary reload, reconnect and repeated clicks preserve the receipt. External effects performed by a custom reward function have the persistence guarantees of that function and its host.

### Give a block as the reward

For a reward of four stone bricks, create `data/workshop/loot_table/quest/stone_bricks.json` in the editable chapter pack:

```json
{
  "type": "minecraft:generic",
  "pools": [{
    "rolls": 1,
    "entries": [{
      "type": "minecraft:item",
      "name": "minecraft:stone_bricks",
      "functions": [{"function": "minecraft:set_count", "count": 4}]
    }]
  }]
}
```

Set the quest advancement's `rewards` to `{"loot":["workshop:quest/stone_bricks"]}` and update its display description so players can see the payout. Build the pack for an automatic reward, or run the manual-claim conversion above on this editable version before building. Test with a fresh player and click **Claim reward** twice. The player should receive four blocks in total.

## Integrate a Horizon gameplay mod

Ship the generated companion ZIP with the native mod. Built-in triggers such as inventory changes work without a Rust callback. For a custom action, let the authoritative server finish the action and commit its inventory change first. Then invoke the job-completed function tag with the credited player as executor and at the appropriate site. The journal handler grants an impossible-trigger advancement to that player. Other mods can append listeners using the same function-tag path and additive values. Use a new /v2/ path when the meaning or calling convention changes.

For a native Horizon host, the API 21 helper native_run_command runs a console command. Construct the following command with the trusted online player's server-provided UUID. The function requires a player executor. In a data-pack function that already runs as that player, call the tag directly.

~~~text
execute as <player-uuid> at @s run function #workshop:api/v1/job_completed
~~~

For an optional journal companion, the host should own an empty data/workshop/tags/function/api/v1/job_completed.json containing {"values":[]}. The separately installed journal pack appends its handler. This gives the host a callable empty tag even when the companion is absent. The host operation must succeed independently of listener return values. A progress event is distinct from a permission check. For gating a machine, collect vetoes synchronously before spending materials, as the bundled Frontier connector does. Player journal progress records personal history. Colony membership, quotas, and permissions belong to their owning server mod.

## Extend an existing chapter

Set a new advancement's parent to the fully qualified ID of an existing node, even across namespaces. Omit a chapter manifest for an extension that only adds children. During development, supply unpacked dependency packs in low-to-high priority order. The final argument pack has the highest priority. Only its own resources enter its output ZIP.

~~~powershell
python journal.py check my-addon --dependency workshop
python journal.py build my-addon my-addon-1.0.zip --dependency workshop
python test_journal.py
~~~

The SDK checks namespaced IDs, parent cycles, missing dependencies, criteria requirements, version and coordinate ranges, duplicate root declarations, and positions outside a chapter. Give custom criteria namespaced trigger IDs. The checks resolve advancement references against the supplied folders. Supply unpacked vanilla resources as a dependency if a parent comes from vanilla. For development with large vanilla packs, extract the referenced parent chain into a small fixture. The game remains the authority on whether a particular trigger, condition, item or reward is registered. Exercise custom behavior in a test world.

For editor completion, associate **chapter-v1.schema.json** with **data/*/quest_chapter/**/*.json** in your editor's JSON schema settings. The manifest accepts version, root, order and positions. Coordinates are signed 16-bit map units. Omitting positions selects automatic layout. Root and child advancements carry normal Minecraft display, criteria and reward data. A child can be granted before its parent unless its gameplay trigger enforces that prerequisite.

## Runtime and compatibility

This release targets Horizon's chapter-aware 26.3 client and server, data-pack format 121 and chapter contract v1. New chapters require only a server data-pack update. Build the matching runtime using the [installation guide](../../README.md#build-the-beta-runtime).

If L opens vanilla advancements, verify the server and client build, the pack listing, and that a displayed root is visible to that player. For a skipped chapter, check server logs for quest_chapter and run the CLI checker with the same dependencies. A regular root tick criterion makes the example visible on joining.

## Gate player crafting

Define a progression_rule file in a mod companion or modpack override. Validate it with journal.py check, passing each --dependency in low-to-high order. Add --resources to check registered items and built-in quests against the target installation. The runtime checks both on world open and reload. See the [author guide](../../docs/quest-gated-crafting.md) and [editor schema](progression-rule-v1.schema.json).
