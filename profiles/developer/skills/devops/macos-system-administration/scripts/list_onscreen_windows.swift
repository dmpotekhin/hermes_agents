// List every window actually on screen (what the user sees), independent of the
// Screen Recording permission that strips windows out of `screencapture` output.
//
// Build + run:
//   swiftc -O list_onscreen_windows.swift -o /tmp/winlist && /tmp/winlist
// The first compile on a CLT-only machine prints "did not find a prebuilt standard
// library ... building it may take a few minutes" — one-time cost, give it a long timeout.
//
// Output: pid, layer, alpha, owner, name, bounds per window, then the PyCharm count.
// layer=0 alpha=1.0 with real bounds => genuinely visible. Window *names* are empty
// unless the caller has Screen Recording permission; pid/owner/bounds are always there.

import CoreGraphics
import Foundation

let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
guard let rawList = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else {
    print("no window list")
    exit(1)
}

print("WINDOWS ON SCREEN: \(rawList.count)")
var pycharmSeen = 0
for window in rawList {
    let owner = window[kCGWindowOwnerName as String] as? String ?? "?"
    let name = window[kCGWindowName as String] as? String ?? ""
    let pid = window[kCGWindowOwnerPID as String] as? Int ?? -1
    let layer = window[kCGWindowLayer as String] as? Int ?? -1
    let alpha = window[kCGWindowAlpha as String] as? Double ?? 0
    var bounds = "?"
    if let box = window[kCGWindowBounds as String] as? [String: Any] {
        let x = box["X"] ?? 0, y = box["Y"] ?? 0
        let w = box["Width"] ?? 0, h = box["Height"] ?? 0
        bounds = "x=\(x) y=\(y) w=\(w) h=\(h)"
    }
    if owner.lowercased().contains("pycharm") { pycharmSeen += 1 }
    print("pid=\(pid) layer=\(layer) alpha=\(alpha) owner=\(owner) name=\(name) bounds=\(bounds)")
}
print("PYCHARM WINDOWS: \(pycharmSeen)")
