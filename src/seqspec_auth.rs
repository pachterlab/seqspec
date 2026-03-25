use crate::auth::{init_profile, AuthKind, AuthProfile, AuthRegistry, RemoteAccess};
use anyhow::Result;
use clap::{Args, Subcommand, ValueEnum};
use serde::Serialize;

#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum OutputFormat {
    Text,
    Json,
}

#[derive(Debug, Args)]
pub struct AuthArgs {
    #[command(subcommand)]
    pub command: AuthCommand,
}

#[derive(Debug, Subcommand)]
pub enum AuthCommand {
    Init(AuthInitArgs),
    Path(AuthPathArgs),
    List(AuthListArgs),
    Resolve(AuthResolveArgs),
}

#[derive(Debug, Args)]
pub struct AuthInitArgs {
    #[arg(long, value_name = "PROFILE", required = true)]
    pub profile: String,

    #[arg(long = "host", value_name = "HOST", required = true)]
    pub hosts: Vec<String>,

    #[arg(long, value_enum, default_value_t = AuthKind::Basic)]
    pub kind: AuthKind,

    #[arg(long, value_name = "ENV", required = true)]
    pub username_env: String,

    #[arg(long, value_name = "ENV", required = true)]
    pub password_env: String,

    #[arg(long, value_enum, default_value_t = OutputFormat::Text)]
    pub format: OutputFormat,
}

#[derive(Debug, Args)]
pub struct AuthPathArgs {
    #[arg(long, value_enum, default_value_t = OutputFormat::Text)]
    pub format: OutputFormat,
}

#[derive(Debug, Args)]
pub struct AuthListArgs {
    #[arg(long, value_enum, default_value_t = OutputFormat::Text)]
    pub format: OutputFormat,
}

#[derive(Debug, Args)]
pub struct AuthResolveArgs {
    #[arg(help = "Remote URL to inspect", value_name = "URL")]
    pub url: String,

    #[arg(long, env = "SEQSPEC_AUTH_PROFILE", value_name = "PROFILE")]
    pub auth_profile: Option<String>,

    #[arg(long, value_enum, default_value_t = OutputFormat::Text)]
    pub format: OutputFormat,
}

#[derive(Debug, Serialize)]
struct PathOutput<'a> {
    kind: &'a str,
    source: &'a str,
    path: Option<String>,
    exists: bool,
}

pub fn run(args: &AuthArgs) -> Result<()> {
    match &args.command {
        AuthCommand::Init(args) => run_init(args),
        AuthCommand::Path(args) => run_path(args),
        AuthCommand::List(args) => run_list(args),
        AuthCommand::Resolve(args) => run_resolve(args),
    }
}

fn run_init(args: &AuthInitArgs) -> Result<()> {
    let output = init_profile(
        &args.profile,
        AuthProfile {
            hosts: args.hosts.clone(),
            kind: args.kind.clone(),
            username_env: args.username_env.clone(),
            password_env: args.password_env.clone(),
        },
    )?;
    print_value(args.format, &output)
}

fn run_path(args: &AuthPathArgs) -> Result<()> {
    let registry = AuthRegistry::load()?;
    let location = registry.location();
    let output = PathOutput {
        kind: "auth_config_path",
        source: &location.source,
        path: location
            .path
            .as_ref()
            .map(|path| path.display().to_string()),
        exists: location.exists,
    };
    print_value(args.format, &output)
}

fn run_list(args: &AuthListArgs) -> Result<()> {
    let registry = AuthRegistry::load()?;
    let profiles = registry.profile_summaries();
    print_value(args.format, &profiles)
}

fn run_resolve(args: &AuthResolveArgs) -> Result<()> {
    let registry = AuthRegistry::load()?;
    let resolved = registry.resolve_summary(&args.url, args.auth_profile.as_deref())?;
    if let Some(profile_name) = args.auth_profile.as_deref() {
        let _ = RemoteAccess::load(Some(profile_name))?;
    }
    print_value(args.format, &resolved)
}

fn print_value<T: Serialize>(format: OutputFormat, value: &T) -> Result<()> {
    match format {
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(value)?);
        }
        OutputFormat::Text => {
            println!("{}", serde_json::to_string_pretty(value)?);
        }
    }
    Ok(())
}
