# Zerocroshair

Crosshair overlay для игр на базе PyQt5.

---

## Скачать готовый EXE

> Перейди в [Releases](https://github.com/Kurt-Yanari/Crosshairover_V2/releases) и скачай последний `Zerocroshair.exe`.

Прямая ссылка (после публикации релиза):
```
https://github.com/Kurt-Yanari/Crosshairover_V2/releases/latest/download/Zerocroshair.exe
```

---

## Установка из исходников

```bash
pip install PyQt5 keyboard
python crosshair_singlefile.py
```

## Сборка EXE

```bash
pip install pyinstaller
```
Затем запусти `build.bat`. EXE появится в `dist\Zerocroshair.exe`.

---

## Возможности

### Типы прицела
- cross, dot, ring (кольцо / dot without center), circle, cross+dot, circle+dot, x, T, chevron, triangle

### Типы оверлея
- Simple Overlay — стандартный
- Real Overlay (DirectX) — для fullscreen игр
- Borderless Window — для borderless windowed
- Always on Top — простой поверх окон

### Прочее
- Обводка (stroke) и внешние линии за краями
- Профили с быстрым выбором через трей
- Горячие клавиши (настраиваются)
- Иконка приложения в трее

---

## Публикация релиза на GitHub

1. Собери EXE: `build.bat`
2. GitHub -> Releases -> Draft a new release
3. Tag: `v1.0.0`, прикрепи `dist/Zerocroshair.exe`
4. Publish release

Ссылка на скачивание будет:
`https://github.com/Kurt-Yanari/Crosshairover_V2/releases/latest/download/Zerocroshair.exe`
