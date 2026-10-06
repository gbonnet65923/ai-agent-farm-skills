# NSIS-установщики: извлечение без прав администратора

## Проблема
Установщики NSIS (Nullsoft Scriptable Install System) требуют прав администратора (UAC elevation).
Тихая установка (`/S`) без прав возвращает `[WinError 740] Запрошенная операция требует повышения`.

## Решение: двухэтапная 7z-экстракция

NSIS-установщики содержат:
1. Заглушку-распаковщик (PE executable)
2. Вложенный 7z-архив с файлами приложения

### Шаг 1: Извлечь внешний контейнер
```bash
7z x "Installer.exe" -o"extracted/" -y
```
→ Результат: `$PLUGINSDIR/` (NSIS-плагины) и `$R0/` (uninstaller)

### Шаг 2: Извлечь вложенный app-64.7z
В `$PLUGINSDIR/` находится `app-64.7z` — это основной архив приложения.
```bash
7z x "extracted/\$PLUGINSDIR/app-64.7z" -o"app/" -y
```

**Важно**: в bash `$` интерпретируется как переменная. Используй Python `subprocess` для избежания экранирования:
```python
import subprocess
subprocess.run([
    r"C:\Program Files\7-Zip\7z.exe", "x",
    r"C:\path\to\extracted\$PLUGINSDIR\app-64.7z",
    "-oC:\path\to\app", "-y"
])
```

### Шаг 3: Запуск приложения
После извлечения приложение — это Electron-приложение с `app.exe` в корне.
```bash
./app/AppName.exe
```
Приложение может запустить автообновление — это нормально.

## Пример: LobsterAI
- Установщик: `LobsterAI-Setup-x64-2026.8.7-official.exe` (244 MB)
- NSIS-заголовок: offset 405972 (`NullsoftInst`)
- Вложенный архив: `app-64.7z` (255 MB)
- После извлечения: 1690 файлов, 443 папки, 1.27 GB
- Главный исполняемый: `LobsterAI.exe` (214 MB)
- Electron BrowserWindow с автообновлением
- Данные: `%APPDATA%/LobsterAI/`

## Альтернативы
- `7z` не установлен: `winget install 7zip` или `choco install 7zip`
- Если `7z` не находит `$PLUGINSDIR`: используй Python с `subprocess` (не bash)
- Второй уровень может быть не `7z`, а `zip` — пробуй и тот и другой