# Two modpacks, one rail press

These are fresh-world profiles for a chapter-aware Horizon 26.3 installation. The ZIP contains the world's datapacks folder and its ordered datapacks.json. Extract one profile into an empty world directory before starting that world. Avoid installing it over an existing world's pack selection. Use a separate world and launcher profile for these examples.

| Profile | First journal chapter | Press access | First batch reward |
| --- | --- | --- | --- |
| Beginner | Field Engineering | Stand on a smithing table with six iron ingots and one stick. Use /trigger eng_press. | 24 rails plus 10 XP |
| Expert | Colony Railworks | Stand on a lodestone and use /trigger col_found. Put a bookshelf one block east of the lodestone, with a lectern on top. Visit as a member, then operate a smithing table within 12 blocks of the charter. | 24 rails plus 3 XP |

Subsequent batches produce 24 rails and spend the same materials. The first-batch XP is granted once per player. Obtaining iron also has its own quest reward in both profiles.

## How the override works

Read profiles.json from left to right. The exporter copies the selected packs and writes their priority explicitly. Beginner uses the engineering mod as shipped. Expert includes Colony Workshop and the Frontier gameplay connector, then loads expert_rules last. That pack supplies the same engineering:field chapter ID with an earlier sort order, the same engineering:press root ID with new display text, and the same engineering:first_batch advancement ID with the expert reward. The colony gate comes from the connector. The press function itself comes from the same engineering pack in both worlds.

For a different experience, edit the expert advancement JSON to change the title, description or XP. Keep the advancement ID to preserve completion history. A player who has already earned the first-batch advancement will not earn its replacement reward retroactively.

From the repository root, export to fresh filenames.

~~~powershell
python examples/press-profiles/export.py beginner beginner-world.zip
python examples/press-profiles/export.py expert expert-world.zip
~~~

The expert profile also includes the Founders journal. Obtain a crafting table to complete **Set Up Camp** and unlock player crafting of blast furnaces. You can claim the XP later. The beginner profile has ordinary blast-furnace crafting. [Crafting rule guide](../../docs/quest-gated-crafting.md)
