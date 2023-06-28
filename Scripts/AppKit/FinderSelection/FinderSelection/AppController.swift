//
//  AppController.swift
//  FinderSelection
//
//  Created by Josh Rideout on 07/06/2023.
//

import Foundation
import AppKit
import Cocoa

class AppController: NSViewController {
    
    convenience init() {
        self.init(nibName: nil, bundle: nil)
    }
    
    override init(nibName nibNameOrNil: NSNib.Name?, bundle nibBundleOrNil: Bundle?) {
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    override func loadView() {
        
        func completion() {
            print(response.jsonString)
            exit(0)
        }
        
        let openPanel = NSOpenPanel()
        openPanel.level = .popUpMenu
        openPanel.canChooseFiles = false
        openPanel.canChooseDirectories = true
        openPanel.allowsMultipleSelection = false
        
        openPanel.begin { result in
            
            guard result == .OK else {
                response.didCancelSelection = true
                completion()
                return
            }
            
            guard let selectedURL = openPanel.url else {
                response.errorMessage = "Unable to obtain the selectee folder path"
                completion()
                return
            }
            
            let selectedFolderPath = selectedURL.path
            response.selectedFolderPath = selectedFolderPath
            completion()
        }
        
    }
    
}
