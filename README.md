# Horizon Quest Journal

A quest book for Horizon 26.3. Press **L** to open a chapter, follow its quest map, and select a quest to see its objective and reward. Mods can contribute chapters and progression events. Modpacks can change rewards and decide which quests unlock crafting recipes.

![The Founders quest map beside the Set Up Camp objective and its Claim reward button](https://raw.githubusercontent.com/Fnux8890/horizon-quest-journal/v1.1.2-beta.1/docs/media/quest-journal/equal-page-spread.png)

## Play the public beta

1. Build the matching Horizon runtime using the [beta installation guide](https://github.com/Fnux8890/horizon-quest-journal/tree/v1.1.2-beta.1#build-the-beta-runtime). Single-player runs locally. Multiplayer requires the patched build on the host and each client.
2. Download the Founders chapter ZIP from the [public beta release](https://github.com/Fnux8890/horizon-quest-journal/releases/tag/v1.1.2-beta.1) and enable it in a fresh world's data packs.
3. Obtain a crafting table, open the journal, select **Set Up Camp**, and click **Claim reward** to collect 10 XP.

The release also includes two example world profiles. Beginner allows ordinary blast furnace crafting. Expert unlocks that recipe when the player completes **Set Up Camp**, even if they wait to claim the XP.

## Build on the journal

- **Mod authors** can generate a chapter with the offline Python CLI, connect a gameplay event, and award items such as stone bricks. Start with the [mod author guide](https://github.com/Fnux8890/horizon-quest-journal/blob/v1.1.2-beta.1/tools/quest-journal/README.md).
- **Modpack authors** can load an override pack last to change a chapter or reward, or add a quest prerequisite to a recipe. See the [crafting rule guide](https://github.com/Fnux8890/horizon-quest-journal/blob/v1.1.2-beta.1/docs/quest-gated-crafting.md) and the [Beginner and Expert examples](https://github.com/Fnux8890/horizon-quest-journal/tree/v1.1.2-beta.1/examples/press-profiles).
- **Contributors** can browse the [tagged beta source](https://github.com/Fnux8890/horizon-quest-journal/tree/v1.1.2-beta.1) and follow the [contribution instructions](https://github.com/Fnux8890/horizon-quest-journal/tree/v1.1.2-beta.1#contribute).
