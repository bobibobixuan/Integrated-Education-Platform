from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT_DIR / 'frontend' / 'dist'
OUTPUT_DIR = ROOT_DIR / 'dist'
OUTPUT_PATH = OUTPUT_DIR / 'Python基础闯关_正式版.html'
APP_BASE = '/app/'


def read_dist_asset(relative_path):
    """Read a file from frontend/dist/. Raises if missing."""
    file_path = FRONTEND_DIST / relative_path
    if not file_path.exists():
        raise FileNotFoundError(f'未找到 dist 资源：{relative_path}')
    return file_path.read_text(encoding='utf-8')


def find_asset(pattern_prefix):
    """Find the first file in frontend/dist/assets/ matching the prefix."""
    assets_dir = FRONTEND_DIST / 'assets'
    if not assets_dir.is_dir():
        raise FileNotFoundError('frontend/dist/assets/ 目录不存在，请先运行 npm run build')
    for path in sorted(assets_dir.iterdir()):
        if path.is_file() and path.name.startswith(pattern_prefix):
            return path.relative_to(FRONTEND_DIST).as_posix()
    raise FileNotFoundError(f'未找到匹配 {pattern_prefix} 的 asset 文件')


def build_game():
    print("Building offline bundle from frontend/dist/ ...")

    if not (FRONTEND_DIST / 'index.html').exists():
        raise FileNotFoundError(
            'frontend/dist/index.html 不存在，请先运行: cd frontend && npm run build'
        )

    html_content = read_dist_asset('index.html')

    # Resolve CSS files referenced in index.html
    index_css = find_asset('index-')
    for marker in ['LoginView-', 'GameView-', 'AdminView-', 'LeaderboardView-',
                   'AchievementsView-', 'PvPLobbyView-', 'PvPBattleView-']:
        try:
            css_path = find_asset(marker)
            css_filename = css_path.split('/')[-1]
            html_content = html_content.replace(
                f'/app/assets/{css_filename}',
                f'{APP_BASE}assets/{css_filename}',
            )
        except FileNotFoundError:
            pass

    # Rewrite asset paths from relative to /app/ base
    html_content = html_content.replace('src="/app/assets/', f'src="{APP_BASE}assets/')
    html_content = html_content.replace('href="/app/assets/', f'href="{APP_BASE}assets/')
    html_content = html_content.replace('href="/app/', f'href="{APP_BASE}')

    # Verify key markers exist
    smoke_markers = [
        '<div id="app">',
        '</html>',
    ]
    missing = [m for m in smoke_markers if m not in html_content]
    if missing:
        raise ValueError(f'打包结果缺少关键标记: {missing}')

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(html_content, encoding='utf-8')
    print(f'Smoke check passed')
    print(f'Build successful: {OUTPUT_PATH.relative_to(ROOT_DIR)}')
    print(f'Note: This bundles index.html only. Copy frontend/dist/ alongside for full SPA assets.')


if __name__ == '__main__':
    build_game()
