from pathlib import Path


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "panel-backend").exists():
        return cwd
    return Path(__file__).resolve().parents[3]


def _env_path(bot_name: str) -> Path:
    return _repo_root() / f"{bot_name}-bot" / ".env"


def _normalize_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1].strip()
    return text


def read_config(bot_name: str) -> dict[str, str]:
    path = _env_path(bot_name)
    if not path.exists():
        return {}

    config: dict[str, str] = {}
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = _normalize_value(value)
    except OSError:
        return {}

    return config


def write_config(bot_name: str, updates: dict[str, str]) -> bool:
    path = _env_path(bot_name)
    try:
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
        else:
            lines = []

        updated_keys: set[str] = set()
        new_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                new_lines.append(line)
                continue

            key, _ = line.split("=", 1)
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
            else:
                new_lines.append(line)

        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}")

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            handle.write("\n".join(new_lines))
            if new_lines:
                handle.write("\n")
        return True
    except OSError:
        return False


def read_divar_config() -> dict[str, str]:
    config = read_config("divar")
    return {
        "DIVAR_MAX_ADS_PER_RUN": config.get("DIVAR_MAX_ADS_PER_RUN", ""),
        "DIVAR_DAILY_MESSAGE_LIMIT": config.get("DIVAR_DAILY_MESSAGE_LIMIT", ""),
        "DIVAR_MIN_DELAY_SECONDS": config.get("DIVAR_MIN_DELAY_SECONDS", ""),
        "DIVAR_MAX_DELAY_SECONDS": config.get("DIVAR_MAX_DELAY_SECONDS", ""),
        "DIVAR_PROFILE_DIR": config.get("DIVAR_PROFILE_DIR", ""),
        "DIVAR_PROFILE_COUNT": config.get("DIVAR_PROFILE_COUNT", ""),
        "HTTP_PROXY": config.get("HTTP_PROXY", ""),
        "DEEPSEEK_API_KEY": config.get("DEEPSEEK_API_KEY", ""),
        "AFRA_API_URL": config.get("AFRA_API_URL", ""),
    }


def read_torob_config() -> dict[str, str]:
    config = read_config("torob")
    return {
        "AFRA_API_URL": config.get("AFRA_API_URL", ""),
        "AFRA_API_KEY": config.get("AFRA_API_KEY", ""),
        "TOROB_MIN_DELAY_SECONDS": config.get("TOROB_MIN_DELAY_SECONDS", ""),
        "TOROB_MAX_DELAY_SECONDS": config.get("TOROB_MAX_DELAY_SECONDS", ""),
        "TOROB_MAX_SELLERS_PER_URL": config.get("TOROB_MAX_SELLERS_PER_URL", ""),
        "SELLER_CRAWL_TIMEOUT_SECONDS": config.get("SELLER_CRAWL_TIMEOUT_SECONDS", ""),
        "CRAWL_SELLER_SITES": config.get("CRAWL_SELLER_SITES", ""),
    }


def read_template() -> str:
    path = _repo_root() / "divar-bot" / "data" / "divar_template.txt"
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def write_template(template: str) -> bool:
    path = _repo_root() / "divar-bot" / "data" / "divar_template.txt"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template, encoding="utf-8")
        return True
    except OSError:
        return False
