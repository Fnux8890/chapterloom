# Chapterloom CLI for Rust developers

Use `quest-journal` to work with Horizon 26.3 journal data packs. Install from a checkout containing this directory, using Cargo:

```sh
cargo install --locked --path tools/quest-journal-rs
```

The installed binary runs independently of Python and the game. Edit the pack in a text editor, use either CLI on an existing pack, or switch between them at any point.

```sh
quest-journal init workshop --namespace workshop --title "Workshop Journal"
quest-journal check workshop
quest-journal manual workshop workshop-claims --quest workshop:first_job
quest-journal build workshop-claims workshop.zip
```

Install `workshop.zip` in a world's `datapacks/` directory. The [author guide](../quest-journal/README.md) explains how to enable the chapter, trigger a custom job, and deliver block rewards.

For a pack that references another pack, pass each unpacked dependency in increasing priority order. Your input folder has the highest priority. To verify item IDs against the target installation, add `--resources <extracted-game-resources>` to `check` or `build`. Only the input pack's files enter its ZIP.

```sh
quest-journal check camp_rules --dependency datapacks/horizon_quests
```

Both CLIs use the same commands and claim IDs. Generated JSON formatting and ZIP compression can differ. Pin one tool and version if your release process compares archive hashes. Each build and manual conversion writes to a new destination. Use ordinary files and directories for pack inputs; the Rust tool rejects symbolic links.

For contributors, build the crate with `cargo build --locked --manifest-path tools/quest-journal-rs/Cargo.toml`. Run the cross-language fixtures with `python tools/quest-journal-rs/test_parity.py <path-to-built-executable>`.
