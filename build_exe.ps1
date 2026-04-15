param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [switch]$OneDir
)

if (-not (Test-Path $Python)) {
    Write-Error "Не найден интерпретатор Python: $Python"
    exit 1
}

& $Python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller не установлен. Установите его командой: $Python -m pip install pyinstaller"
    exit 1
}

$arguments = @(
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--name",
    "DynamicGamesApp",
    "--windowed",
    "--collect-data",
    "matplotlib",
    "--collect-submodules",
    "matplotlib.backends"
)

if (-not $OneDir) {
    $arguments += "--onefile"
}

$arguments += "gui_main.py"

& $Python @arguments
