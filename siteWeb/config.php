<?php
/**
 * config.php — Single source of truth for the frontend.
 *
 * Reads the .env file once and exposes its values both to PHP
 * (via the $CONFIG array / cfg()) and to the browser (via window.APP_CONFIG,
 * injected by render_js_config() into the page <head>).
 *
 * Usage in a PHP page:
 *   require_once __DIR__ . '/config.php';   // at the very top
 *   ...
 *   <head>
 *     <?php render_js_config(); ?>          // before any app .js
 *   </head>
 */

/**
 * Minimal .env parser (no external dependency).
 * Returns an associative array of KEY => value.
 */
function load_env(string $path): array {
    $env = [];
    if (!is_file($path)) {
        return $env;
    }
    foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        // skip comments and malformed lines
        if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
            continue;
        }
        [$key, $value] = explode('=', $line, 2);
        $key   = trim($key);
        $value = trim(trim($value), "\"'");   // trim spaces then surrounding quotes
        $env[$key] = $value;
    }
    return $env;
}

// Load .env located next to this file
$CONFIG = load_env(__DIR__ . '/.env');

/**
 * Read a config value with a fallback default.
 */
function cfg(string $key, $default = '') {
    global $CONFIG;
    return $CONFIG[$key] ?? $default;
}

/**
 * Build the full base URLs the browser needs from the .env parts.
 */
function api_base_url(): string {
    return cfg('API_SCHEME', 'http') . '://' . cfg('API_HOST', 'localhost') . ':' . cfg('API_PORT', '8000');
}
function ws_base_url(): string {
    return cfg('WS_SCHEME', 'ws') . '://' . cfg('API_HOST', 'localhost') . ':' . cfg('API_PORT', '8000');
}

/**
 * Inject the JS config object into the page.
 * Call this in <head>, BEFORE loading any application .js file.
 * Every .js file then reads from window.APP_CONFIG instead of
 * hardcoding URLs or thresholds.
 */
function render_js_config(): void {
    $jsConfig = [
        'API_BASE'  => api_base_url(),                       // e.g. http://localhost:8000
        'WS_BASE'   => ws_base_url(),                        // e.g. ws://localhost:8000
        'THRESHOLD' => (float) cfg('THRESHOLD', '0.61'),     // operational threshold
    ];
    // JSON_UNESCAPED_SLASHES keeps URLs readable in the page source
    echo '<script>window.APP_CONFIG = '
        . json_encode($jsConfig, JSON_UNESCAPED_SLASHES)
        . ';</script>' . PHP_EOL;
}