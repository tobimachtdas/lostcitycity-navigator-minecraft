#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead,BufReader},process::{Child,ChildStdin,Command,Stdio},sync::Mutex};
use tauri::{Manager,WebviewUrl,WebviewWindowBuilder};
#[cfg(windows)] use std::os::windows::process::CommandExt;
struct Backend(Mutex<Option<(Child,ChildStdin)>>);
fn main(){
 tauri::Builder::default().setup(|app|{
  let exe=std::env::current_exe()?;
  let sidecar=exe.parent().ok_or("Programmordner fehlt")?.join("lcf-backend.exe");
  let mut command=if sidecar.is_file(){Command::new(sidecar)}else if cfg!(debug_assertions){
   let root=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
   let mut c=Command::new(std::env::var("LCF_PYTHON").unwrap_or_else(|_|"python".into()));
   c.arg(root.join("desktop/webapp.py")); c
  }else{return Err("Scanner fehlt neben der Anwendung. Bitte neu installieren.".into());};
  command.arg("--parent-pipe").stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
  #[cfg(windows)] command.creation_flags(0x08000000);
  let mut child=command.spawn()?;
  let stdin=child.stdin.take().ok_or("Scanner-Eingabe fehlt")?;
  let mut line=String::new();
  BufReader::new(child.stdout.take().ok_or("Scanner-Ausgabe fehlt")?).read_line(&mut line)?;
  if !line.starts_with("http://127.0.0.1:"){drop(stdin);let _=child.kill();return Err("Lokaler Scanner konnte nicht gestartet werden".into());}
  app.manage(Backend(Mutex::new(Some((child,stdin)))));
  WebviewWindowBuilder::new(app,"main",WebviewUrl::External(line.trim().parse()?)).title("Lost City Finder · by tobimachtdas").inner_size(1500.,900.).min_inner_size(900.,650.).build()?;
  Ok(())
 }).build(tauri::generate_context!()).expect("Tauri Start fehlgeschlagen").run(|handle,event|{if let tauri::RunEvent::Exit=event{if let Some(b)=handle.try_state::<Backend>(){if let Ok(mut b)=b.0.lock(){if let Some((mut child,stdin))=b.take(){drop(stdin);std::thread::spawn(move||{let _=child.wait();});}}}}});
}
