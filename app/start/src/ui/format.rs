pub const RED: &str = "\x1b[0;31m";
pub const GREEN: &str = "\x1b[0;32m";
pub const YELLOW: &str = "\x1b[1;33m";
pub const BLUE: &str = "\x1b[0;34m";
pub const NC: &str = "\x1b[0m";

pub fn log(msg: &str) {
    println!("{}[job-search]{} {}", BLUE, NC, msg);
}

pub fn warn(msg: &str) {
    println!("{}[job-search]{} {}", YELLOW, NC, msg);
}

pub fn err(msg: &str) {
    println!("{}[job-search]{} {}", RED, NC, msg);
}

pub fn ok(msg: &str) {
    println!("{}[job-search]{} {}", GREEN, NC, msg);
}

pub fn header(msg: &str) {
    println!();
    println!("{}═══ {} ═══{}", BLUE, msg, NC);
    println!();
}

pub fn section(msg: &str) {
    println!("  {}{}{}", YELLOW, msg, NC);
}
