#![allow(warnings)]
#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(dead_code)]

use seqspec::seqspec_version;
use seqspec::seqspec_format;
use seqspec::utils;

use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[clap(name = "seqspec", version = "0.X.0", author = "Your Name")]
struct Args {
    #[command(subcommand)]
    subcmd: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Version(seqspec_version::VersionArgs),
    Format(seqspec_format::FormatArgs),
    // other subcommands later...
}

fn main() {
    let args = Args::parse();
    match args.subcmd {
        Commands::Version(args) => seqspec_version::validate_version_args(&args),
        Commands::Format(args) => seqspec_format::validate_format_args(&args),
    }
}