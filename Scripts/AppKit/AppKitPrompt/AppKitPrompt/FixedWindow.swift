//
//  FixedWindow.swift
//  AppKitPrompt
//
//  Created by Josh Rideout on 17/04/2023.
//

import AppKit
import Cocoa

final class FixedWindow: NSWindow {
    
    private let onExit: () -> Void
    private var windowContent: WindowContentViewController!
    
    init(size: NSRect, onExit: @escaping () -> Void) {
        self.onExit = onExit
        
        super.init(
            contentRect: size,
            styleMask: [
                .titled
            ],
            backing: .buffered,
            defer: false
        )
        
        windowContent = WindowContentViewController(
            onExit: onExit
        )
        windowContent.view.frame = NSRect(origin: .zero, size: windowSize)
        
        title = args.promptTitle
        
        // Forces the window to be shown above other opened applications
        level = .floating
        
        contentViewController = windowContent
    }
    
    func focusOnText() {
        becomeFirstResponder()
    }
}

