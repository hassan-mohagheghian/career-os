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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_constants_not_empty() {
        assert!(!RED.is_empty());
        assert!(!GREEN.is_empty());
        assert!(!YELLOW.is_empty());
        assert!(!BLUE.is_empty());
        assert!(!NC.is_empty());
    }

    #[test]
    fn test_reset_terminates_colors() {
        assert_eq!(NC, "\x1b[0m");
        assert!(RED.starts_with("\x1b["));
        assert!(GREEN.starts_with("\x1b["));
        assert!(YELLOW.starts_with("\x1b["));
        assert!(BLUE.starts_with("\x1b["));
    }

    #[test]
    fn test_functions_do_not_panic() {
        log("test log");
        warn("test warn");
        err("test err");
        ok("test ok");
        header("test header");
        section("test section");
    }
}
