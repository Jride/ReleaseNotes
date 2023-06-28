//
//  main.swift
//  AppKitPrompt
//
//  Created by Josh Rideout on 17/04/2023.
//

import AppKit
import Cocoa
import CoreGraphics

var response = Response()
var args = Arguments.decodeCommandLine()

let app = NSApplication.shared
app.setActivationPolicy(.regular)

let screenFrame = NSScreen.main!.frame

let windowWidth: CGFloat = 400
let windowHeight: CGFloat = 200

let windowSize = NSSize(width: windowWidth, height: windowHeight)
let windowFrame = NSRect(
    x: screenFrame.midX - windowWidth/2,
    y: screenFrame.midY - windowHeight/2,
    width: windowWidth,
    height: windowHeight
)

let fixedWindow = FixedWindow(
    size: windowFrame,
    onExit: {
        // Send the exit signal to kill the script
        print(response.jsonString)
        exit(0)
    }
)

// Displays the window
fixedWindow.makeKeyAndOrderFront(app)
fixedWindow.backgroundColor = NSColor(.init(red: 0.06, green: 0.17, blue: 0.24))

app.activate(ignoringOtherApps: true)
app.run()
