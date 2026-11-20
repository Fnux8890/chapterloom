mod author;
mod pack;
mod validate;

use anyhow::Result;
use clap::{Args, Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(version, about = "Author Horizon Quest Journal data packs")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Args)]
struct Inputs {
    folder: PathBuf,
    /// Lower-priority unpacked pack (repeat in increasing priority order).
    #[arg(long)]
    dependency: Vec<PathBuf>,
    /// Extracted game resources containing items.json and data/.
    #[arg(long)]
    resources: Option<PathBuf>,
}

#[derive(Subcommand)]
enum Command {
    /// Create a playable example chapter.
    Init {
        folder: PathBuf,
        #[arg(long)]
        namespace: String,
        #[arg(long)]
        title: String,
    },
    /// Validate chapters, progression rules, and references.
    Check(Inputs),
    /// Validate and package the input folder as a reproducible ZIP.
    Build {
        #[command(flatten)]
        inputs: Inputs,
        output: PathBuf,
    },
    /// Create a copy of a pack with click-to-claim rewards.
    Manual {
        folder: PathBuf,
        output: PathBuf,
        #[arg(long, required = true)]
        quest: Vec<String>,
    },
}

fn main() -> Result<()> {
    match Cli::parse().command {
        Command::Init {
            folder,
            namespace,
            title,
        } => author::init(&folder, &namespace, &title)?,
        Command::Manual {
            folder,
            output,
            quest,
        } => author::manual(&folder, &output, &quest)?,
        Command::Check(inputs) => {
            let (chapters, quests) = validate::check(&inputs)?;
            println!("OK: {chapters} chapter(s), {quests} advancement(s)");
        }
        Command::Build { inputs, output } => {
            validate::check(&inputs)?;
            pack::archive(&inputs.folder, &output)?;
            println!("Built {}", output.display());
        }
    }
    Ok(())
}
