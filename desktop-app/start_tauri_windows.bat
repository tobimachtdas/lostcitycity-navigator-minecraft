@echo off
cd /d "%~dp0"
where cargo >nul 2>&1 || (echo Rust fehlt. Bitte README lesen. & pause & exit /b 1)
cargo run --manifest-path src-tauri\Cargo.toml
pause
