use std::fs;
use std::path::PathBuf;

fn main() {
    println!("cargo:rerun-if-changed=build.rs");

    let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let repo_root = manifest_dir.parent().unwrap().parent().unwrap();
    let binary_name = std::env::var("CARGO_PKG_NAME").unwrap();

    let profile = std::env::var("PROFILE").unwrap_or_else(|_| "release".to_string());

    let target_dir = repo_root.join("app").join("start").join("target").join(&profile);
    let binary = target_dir.join(&binary_name);
    let dest = repo_root.join(&binary_name);

    if binary.exists() {
        let _ = fs::copy(&binary, &dest);
    }
}
