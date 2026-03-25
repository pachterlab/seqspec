#![allow(warnings)]
#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(dead_code)]

use seqspec::seqspec_version;
use seqspec::seqspec_auth;
use seqspec::seqspec_format;
use seqspec::seqspec_find;
use seqspec::seqspec_index;
use seqspec::seqspec_file;
use seqspec::seqspec_split;
use seqspec::seqspec_info;
use seqspec::seqspec_init;
use seqspec::seqspec_methods;
use seqspec::seqspec_modify;
use seqspec::seqspec_upgrade;
use seqspec::seqspec_insert;
use seqspec::seqspec_check;
use seqspec::seqspec_onlist;
use seqspec::utils;

use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(name = "seqspec", version)]
struct Args {
    #[command(subcommand)]
    subcmd: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Auth(seqspec_auth::AuthArgs),
    Version(seqspec_version::VersionArgs),
    Format(seqspec_format::FormatArgs),
    Find(seqspec_find::FindArgs),
    Index(seqspec_index::IndexArgs),
    File(seqspec_file::FileArgs),
    Split(seqspec_split::SplitArgs),
    Info(seqspec_info::InfoArgs),
    Init(seqspec_init::InitArgs),
    Methods(seqspec_methods::MethodsArgs),
    Modify(seqspec_modify::ModifyArgs),
    Upgrade(seqspec_upgrade::UpgradeArgs),
    Insert(seqspec_insert::InsertArgs),
    Check(seqspec_check::CheckArgs),
    Onlist(seqspec_onlist::OnlistArgs),
    // other subcommands later...
}

fn main() {
    let args = Args::parse();
    match args.subcmd {
        Commands::Auth(args) => seqspec_auth::run(&args).unwrap(),
        Commands::Version(args) => seqspec_version::run_version(&args),
        Commands::Format(args) => seqspec_format::run_format(&args),
        Commands::Find(args) => seqspec_find::run_find(&args),
        Commands::Index(args) => seqspec_index::run_index(&args),
        Commands::File(args) => seqspec_file::run_file(&args)
        ,Commands::Split(args) => seqspec_split::run_split(&args)
        ,Commands::Info(args) => seqspec_info::run_info(&args)
        ,Commands::Init(args) => seqspec_init::run_init(&args)
        ,Commands::Methods(args) => seqspec_methods::run_methods(&args)
        ,Commands::Modify(args) => seqspec_modify::run_modify(&args)
        ,Commands::Upgrade(args) => seqspec_upgrade::run_upgrade(&args)
        ,Commands::Insert(args) => seqspec_insert::run_insert(&args)
        ,Commands::Check(args) => { seqspec_check::run_check(&args); }
        ,Commands::Onlist(args) => seqspec_onlist::run_onlist(&args)
    }
}
