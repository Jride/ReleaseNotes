//
//  AppWindow.swift
//  FinderSelection
//
//  Created by Josh Rideout on 07/06/2023.
//

import Foundation
import AppKit

class AppWindow: NSWindow {
    
    init() {
        
        super.init(
            contentRect: .zero,
            styleMask: [
                .fullScreen,
            ],
            backing: .buffered,
            defer: false
        )
        
        // Forces the window to be shown above other opened applications
        level = .floating
        
        contentViewController = AppController()
    }
    
}
