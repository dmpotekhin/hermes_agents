// Список окон, реально видимых на экране (CGWindowList).
//
// Зачем: `screencapture` возвращает одни обои, если у вызвавшего процесса нет
// разрешения Screen Recording (признак — на снимке нет строки меню и окон
// пользователя). По такому скриншоту НЕЛЬЗЯ судить, открылось ли приложение.
//
// Сборка и запуск:
//   swiftc -O winlist.swift -o /tmp/winlist && /tmp/winlist [подстрока-владельца]
// Первая сборка печатает remark про prebuilt standard library и идёт ~минуту —
// это норма. Имена окон пустые без разрешения Screen Recording (не ошибка),
// pid / владелец / геометрия доступны всегда.

import CoreGraphics
import Foundation

let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
guard let windows = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else {
    print("не удалось получить список окон")
    exit(1)
}

let ownerFilter = CommandLine.arguments.count > 1 ? CommandLine.arguments[1].lowercased() : ""

print("WINDOWS ON SCREEN: \(windows.count)")
for window in windows {
    let owner = (window[kCGWindowOwnerName as String] as? String) ?? "?"
    if !ownerFilter.isEmpty && !owner.lowercased().contains(ownerFilter) {
        continue
    }
    let name = (window[kCGWindowName as String] as? String) ?? ""
    let pid = (window[kCGWindowOwnerPID as String] as? Int) ?? -1
    let layer = (window[kCGWindowLayer as String] as? Int) ?? -1
    let alpha = (window[kCGWindowAlpha as String] as? Double) ?? 0
    var bounds = "?"
    if let box = window[kCGWindowBounds as String] as? [String: Any] {
        let x = box["X"] ?? 0, y = box["Y"] ?? 0
        let w = box["Width"] ?? 0, h = box["Height"] ?? 0
        bounds = "x=\(x) y=\(y) w=\(w) h=\(h)"
    }
    print("pid=\(pid) layer=\(layer) alpha=\(alpha) owner=\(owner) name=\(name) bounds=\(bounds)")
}
