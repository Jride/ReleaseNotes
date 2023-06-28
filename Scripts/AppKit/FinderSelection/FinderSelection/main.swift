//
//  main.swift
//  FinderSelection
//
//  Created by Josh Rideout on 07/06/2023.
//

import Foundation
import Cocoa
import AppKit

var response = Response()

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

// Displays the window
let appWindow = AppWindow()
appWindow.makeKeyAndOrderFront(nil)
appWindow.backgroundColor = .clear

app.activate(ignoringOtherApps: true)
app.run()
