use anyhow::{anyhow, bail, Context, Result};
use clap::ValueEnum;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::io::Read as IoRead;
use std::path::PathBuf;
use std::process::{Command, Stdio};

const AUTH_CONFIG_ENV: &str = "SEQSPEC_AUTH_CONFIG";

#[derive(Debug, Clone, Serialize)]
pub struct ConfigLocation {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path: Option<PathBuf>,
    pub source: String,
    pub exists: bool,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
struct AuthConfigFile {
    #[serde(default)]
    profiles: BTreeMap<String, AuthProfile>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq, Eq, ValueEnum)]
#[serde(rename_all = "lowercase")]
pub enum AuthKind {
    Basic,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq, Eq)]
pub struct AuthProfile {
    #[serde(default)]
    pub hosts: Vec<String>,
    pub kind: AuthKind,
    pub username_env: String,
    pub password_env: String,
}

#[derive(Debug, Clone)]
pub struct AuthRegistry {
    location: ConfigLocation,
    profiles: BTreeMap<String, AuthProfile>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct ProfileSummary {
    pub name: String,
    pub kind: AuthKind,
    pub hosts: Vec<String>,
    pub username_env: String,
    pub username_present: bool,
    pub password_env: String,
    pub password_present: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct ResolvedProfileSummary {
    pub url: String,
    pub host: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub profile: Option<ProfileSummary>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct InitProfileOutput {
    pub profile: String,
    pub path: PathBuf,
    pub created_config: bool,
    pub updated_profile: bool,
    pub hosts: Vec<String>,
    pub kind: AuthKind,
    pub username_env: String,
    pub password_env: String,
}

#[derive(Debug, Clone)]
pub struct RemoteAccess {
    registry: AuthRegistry,
    selected_profile: Option<String>,
}

#[derive(Debug, Clone)]
struct ResolvedCredentials {
    username: String,
    password: String,
}

impl AuthRegistry {
    pub fn load() -> Result<Self> {
        let location = config_location();
        let profiles = load_profiles(&location)?;
        Ok(Self { location, profiles })
    }

    pub fn location(&self) -> &ConfigLocation {
        &self.location
    }

    pub fn profile_summaries(&self) -> Vec<ProfileSummary> {
        self.profiles
            .iter()
            .map(|(name, profile)| ProfileSummary {
                name: name.clone(),
                kind: profile.kind.clone(),
                hosts: profile.hosts.clone(),
                username_env: profile.username_env.clone(),
                username_present: env::var_os(&profile.username_env).is_some(),
                password_env: profile.password_env.clone(),
                password_present: env::var_os(&profile.password_env).is_some(),
            })
            .collect()
    }

    pub fn resolve_summary(
        &self,
        url: &str,
        selected_profile: Option<&str>,
    ) -> Result<ResolvedProfileSummary> {
        let host = host_from_url(url)?;
        let profile = self
            .resolve_profile(&host, selected_profile)?
            .map(|(name, profile)| ProfileSummary {
                name,
                kind: profile.kind.clone(),
                hosts: profile.hosts.clone(),
                username_env: profile.username_env.clone(),
                username_present: env::var_os(&profile.username_env).is_some(),
                password_env: profile.password_env.clone(),
                password_present: env::var_os(&profile.password_env).is_some(),
            });
        Ok(ResolvedProfileSummary {
            url: url.to_string(),
            host,
            profile,
        })
    }

    fn resolve_credentials(
        &self,
        url: &str,
        selected_profile: Option<&str>,
    ) -> Result<Option<ResolvedCredentials>> {
        let host = host_from_url(url)?;
        let Some((profile_name, profile)) = self.resolve_profile(&host, selected_profile)? else {
            return Ok(None);
        };

        let username = env::var(&profile.username_env).with_context(|| {
            format!(
                "auth profile '{}' requires env var '{}' for host '{}'",
                profile_name, profile.username_env, host
            )
        })?;
        let password = env::var(&profile.password_env).with_context(|| {
            format!(
                "auth profile '{}' requires env var '{}' for host '{}'",
                profile_name, profile.password_env, host
            )
        })?;

        Ok(Some(ResolvedCredentials { username, password }))
    }

    fn resolve_profile(
        &self,
        host: &str,
        selected_profile: Option<&str>,
    ) -> Result<Option<(String, &AuthProfile)>> {
        if let Some(profile_name) = selected_profile {
            let profile = self.profiles.get(profile_name).ok_or_else(|| {
                anyhow!(
                    "auth profile '{}' is not defined in {}",
                    profile_name,
                    display_config_path(&self.location)
                )
            })?;
            if !profile.matches_host(host) {
                bail!(
                    "auth profile '{}' does not match host '{}'",
                    profile_name,
                    host
                );
            }
            return Ok(Some((profile_name.to_string(), profile)));
        }

        let matches: Vec<(String, &AuthProfile)> = self
            .profiles
            .iter()
            .filter(|(_, profile)| profile.matches_host(host))
            .map(|(name, profile)| (name.clone(), profile))
            .collect();

        match matches.len() {
            0 => Ok(None),
            1 => Ok(matches.into_iter().next()),
            _ => {
                let names = matches
                    .into_iter()
                    .map(|(name, _)| name)
                    .collect::<Vec<_>>()
                    .join(", ");
                bail!("multiple auth profiles match host '{}': {}", host, names)
            }
        }
    }
}

impl AuthProfile {
    fn matches_host(&self, host: &str) -> bool {
        self.hosts
            .iter()
            .any(|candidate| candidate.eq_ignore_ascii_case(host))
    }
}

impl RemoteAccess {
    pub fn anonymous() -> Self {
        Self {
            registry: AuthRegistry {
                location: ConfigLocation {
                    path: None,
                    source: "anonymous".to_string(),
                    exists: false,
                },
                profiles: BTreeMap::new(),
            },
            selected_profile: None,
        }
    }

    pub fn load(selected_profile: Option<&str>) -> Result<Self> {
        let registry = AuthRegistry::load()?;
        if let Some(profile_name) = selected_profile {
            if !registry.profiles.contains_key(profile_name) {
                bail!(
                    "auth profile '{}' is not defined in {}",
                    profile_name,
                    display_config_path(registry.location())
                );
            }
        }
        Ok(Self {
            registry,
            selected_profile: selected_profile.map(|profile| profile.to_string()),
        })
    }

    pub fn with_reader<T, F>(&self, url: &str, read_fn: F) -> Result<T>
    where
        F: FnOnce(Box<dyn IoRead>) -> Result<T>,
    {
        let credentials = self
            .registry
            .resolve_credentials(url, self.selected_profile.as_deref())?;

        let mut command = Command::new("curl");
        command.arg("-fsSL");
        if let Some(credentials) = credentials {
            command
                .arg("--user")
                .arg(format!("{}:{}", credentials.username, credentials.password));
        }
        command
            .arg(url)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let mut child = command
            .spawn()
            .with_context(|| format!("failed to spawn curl for '{}'", url))?;

        let mut stderr = child
            .stderr
            .take()
            .ok_or_else(|| anyhow!("curl did not provide stderr for '{}'", url))?;

        let read_result = {
            let stdout = child
                .stdout
                .take()
                .ok_or_else(|| anyhow!("curl did not provide stdout for '{}'", url))?;
            read_fn(Box::new(stdout))
        };

        let status = child
            .wait()
            .with_context(|| format!("failed to wait for curl while reading '{}'", url))?;

        let mut stderr_text = String::new();
        let _ = stderr.read_to_string(&mut stderr_text);
        let stderr_text = stderr_text.trim();

        match (read_result, status.success()) {
            (Ok(value), true) => Ok(value),
            (Ok(_), false) => {
                if stderr_text.is_empty() {
                    bail!("curl exited with status {} while reading '{}'", status, url);
                }
                bail!(
                    "curl exited with status {} while reading '{}': {}",
                    status,
                    url,
                    stderr_text
                );
            }
            (Err(err), true) => Err(err),
            (Err(err), false) => {
                if stderr_text.is_empty() {
                    Err(err.context(format!(
                        "curl exited with status {} while reading '{}'",
                        status, url
                    )))
                } else {
                    Err(err.context(format!(
                        "curl exited with status {} while reading '{}': {}",
                        status, url, stderr_text
                    )))
                }
            }
        }
    }

    pub fn url_exists(&self, url: &str) -> Result<bool> {
        let credentials = self
            .registry
            .resolve_credentials(url, self.selected_profile.as_deref())?;

        let mut command = Command::new("curl");
        command.arg("-fsSL");
        command.arg("-r").arg("0-0");
        command.arg("-o").arg("/dev/null");
        if let Some(credentials) = credentials {
            command
                .arg("--user")
                .arg(format!("{}:{}", credentials.username, credentials.password));
        }
        command.arg(url).stderr(Stdio::piped());

        let output = command
            .output()
            .with_context(|| format!("failed to spawn curl for '{}'", url))?;

        if output.status.success() {
            return Ok(true);
        }

        let stderr_text = String::from_utf8_lossy(&output.stderr);
        let stderr_text = stderr_text.trim();
        if stderr_text.contains("404") || stderr_text.contains("403") {
            return Ok(false);
        }
        Ok(false)
    }
}

pub fn init_profile(profile_name: &str, profile: AuthProfile) -> Result<InitProfileOutput> {
    let location = config_location();
    let path = location
        .path
        .clone()
        .ok_or_else(|| anyhow!("no auth config path is available on this system"))?;

    let mut config = if path.exists() {
        read_config_file(&path)?
    } else {
        AuthConfigFile::default()
    };

    let created_config = !path.exists();
    let updated_profile = config.profiles.contains_key(profile_name);
    config
        .profiles
        .insert(profile_name.to_string(), profile.clone());

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).with_context(|| {
            format!(
                "failed to create auth config directory '{}'",
                parent.display()
            )
        })?;
    }

    let text = toml::to_string_pretty(&config)
        .with_context(|| format!("failed to serialize auth config '{}'", path.display()))?;
    fs::write(&path, text)
        .with_context(|| format!("failed to write auth config '{}'", path.display()))?;

    Ok(InitProfileOutput {
        profile: profile_name.to_string(),
        path,
        created_config,
        updated_profile,
        hosts: profile.hosts,
        kind: profile.kind,
        username_env: profile.username_env,
        password_env: profile.password_env,
    })
}

fn config_location() -> ConfigLocation {
    if let Some(path) = env::var_os(AUTH_CONFIG_ENV).map(PathBuf::from) {
        return ConfigLocation {
            exists: path.exists(),
            path: Some(path),
            source: format!("env:{}", AUTH_CONFIG_ENV),
        };
    }

    if let Some(base) = env::var_os("XDG_CONFIG_HOME").map(PathBuf::from) {
        let path = base.join("seqspec").join("auth.toml");
        return ConfigLocation {
            exists: path.exists(),
            path: Some(path),
            source: "xdg_config_home".to_string(),
        };
    }

    if let Some(home) = env::var_os("HOME").map(PathBuf::from) {
        let path = home.join(".config").join("seqspec").join("auth.toml");
        return ConfigLocation {
            exists: path.exists(),
            path: Some(path),
            source: "home_default".to_string(),
        };
    }

    ConfigLocation {
        path: None,
        source: "unavailable".to_string(),
        exists: false,
    }
}

fn load_profiles(location: &ConfigLocation) -> Result<BTreeMap<String, AuthProfile>> {
    let Some(path) = &location.path else {
        return Ok(BTreeMap::new());
    };

    if !path.exists() {
        if location.source.starts_with("env:") {
            bail!("auth config does not exist: {}", path.display());
        }
        return Ok(BTreeMap::new());
    }

    let parsed = read_config_file(path)?;
    Ok(parsed.profiles)
}

fn read_config_file(path: &PathBuf) -> Result<AuthConfigFile> {
    let text = fs::read_to_string(path)
        .with_context(|| format!("failed to read auth config '{}'", path.display()))?;
    toml::from_str(&text)
        .with_context(|| format!("failed to parse auth config '{}'", path.display()))
}

fn host_from_url(url: &str) -> Result<String> {
    let (_, rest) = url
        .split_once("://")
        .ok_or_else(|| anyhow!("URL '{}' does not contain a scheme", url))?;
    let authority = rest
        .split('/')
        .next()
        .ok_or_else(|| anyhow!("URL '{}' does not contain an authority", url))?;
    let without_userinfo = authority.rsplit('@').next().unwrap_or(authority);

    let host = if without_userinfo.starts_with('[') {
        let end = without_userinfo
            .find(']')
            .ok_or_else(|| anyhow!("URL '{}' has an invalid IPv6 host", url))?;
        &without_userinfo[1..end]
    } else {
        without_userinfo
            .split(':')
            .next()
            .ok_or_else(|| anyhow!("URL '{}' has an invalid host", url))?
    };

    if host.is_empty() {
        bail!("URL '{}' has an empty host", url);
    }

    Ok(host.to_ascii_lowercase())
}

fn display_config_path(location: &ConfigLocation) -> String {
    location
        .path
        .as_ref()
        .map(|path| path.display().to_string())
        .unwrap_or_else(|| "<unavailable>".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::path::Path;
    use std::sync::{Mutex, OnceLock};
    use std::thread;

    fn env_lock() -> &'static Mutex<()> {
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        LOCK.get_or_init(|| Mutex::new(()))
    }

    fn write_config(root: &Path, text: &str) -> PathBuf {
        let path = root.join("auth.toml");
        fs::write(&path, text).unwrap();
        path
    }

    #[test]
    fn test_registry_loads_profiles_from_env_path() {
        let _guard = env_lock().lock().unwrap();
        let root = env::temp_dir().join(format!(
            "seqspec-auth-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = write_config(
            &root,
            r#"
[profiles.igvf]
hosts = ["api.data.igvf.org", "data.igvf.org"]
kind = "basic"
username_env = "IGVF_ACCESS_KEY_ID"
password_env = "IGVF_ACCESS_KEY_SECRET"
"#,
        );

        env::set_var(AUTH_CONFIG_ENV, &path);
        let registry = AuthRegistry::load().unwrap();
        env::remove_var(AUTH_CONFIG_ENV);

        assert_eq!(registry.profile_summaries().len(), 1);
        assert_eq!(registry.profile_summaries()[0].name, "igvf");

        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn test_resolve_summary_matches_host() {
        let _guard = env_lock().lock().unwrap();
        let root = env::temp_dir().join(format!(
            "seqspec-auth-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = write_config(
            &root,
            r#"
[profiles.igvf]
hosts = ["api.data.igvf.org"]
kind = "basic"
username_env = "IGVF_ACCESS_KEY_ID"
password_env = "IGVF_ACCESS_KEY_SECRET"
"#,
        );
        env::set_var(AUTH_CONFIG_ENV, &path);
        let registry = AuthRegistry::load().unwrap();
        env::remove_var(AUTH_CONFIG_ENV);

        let resolved = registry
            .resolve_summary("https://api.data.igvf.org/reference-files/foo", None)
            .unwrap();

        assert_eq!(resolved.host, "api.data.igvf.org");
        assert_eq!(resolved.profile.unwrap().name, "igvf");

        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn test_remote_access_sends_basic_auth() {
        let _guard = env_lock().lock().unwrap();
        let root = env::temp_dir().join(format!(
            "seqspec-auth-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = write_config(
            &root,
            r#"
[profiles.local]
hosts = ["127.0.0.1"]
kind = "basic"
username_env = "SEQSPEC_TEST_USER"
password_env = "SEQSPEC_TEST_PASS"
"#,
        );
        env::set_var(AUTH_CONFIG_ENV, &path);
        env::set_var("SEQSPEC_TEST_USER", "alice");
        env::set_var("SEQSPEC_TEST_PASS", "secret");

        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let addr = listener.local_addr().unwrap();
        let server = thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            let mut buffer = [0_u8; 4096];
            let size = stream.read(&mut buffer).unwrap();
            let request = String::from_utf8_lossy(&buffer[..size]);
            let authorized = request.contains("Authorization: Basic YWxpY2U6c2VjcmV0");
            let (status, body) = if authorized {
                ("200 OK", "AAAA\nCCCC\n")
            } else {
                ("401 Unauthorized", "missing auth\n")
            };
            let response = format!(
                "HTTP/1.1 {}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                status,
                body.len(),
                body
            );
            stream.write_all(response.as_bytes()).unwrap();
        });

        let access = RemoteAccess::load(Some("local")).unwrap();
        let text = access
            .with_reader(&format!("http://{}/barcodes.txt", addr), |mut reader| {
                let mut text = String::new();
                reader.read_to_string(&mut text)?;
                Ok(text)
            })
            .unwrap();

        env::remove_var(AUTH_CONFIG_ENV);
        env::remove_var("SEQSPEC_TEST_USER");
        env::remove_var("SEQSPEC_TEST_PASS");

        server.join().unwrap();

        assert_eq!(text, "AAAA\nCCCC\n");
        fs::remove_dir_all(root).unwrap();
    }
}
