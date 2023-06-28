//
//  Response.swift
//  FinderSelection
//
//  Created by Josh Rideout on 07/06/2023.
//

import Foundation

struct Response {
    var errorMessage: String? = nil
    var selectedFolderPath: String = ""
    var didCancelSelection: Bool = false
    var logs = [String]()
    
    var jsonString: String {
        
        var json = [String: Any]()
        
        if let err = errorMessage {
            json["error"] = err
        }
        
        json["selected_folder_path"] = selectedFolderPath
        json["did_cancel_selection"] = didCancelSelection.description.lowercased()
        json["logs"] = logs
        
        if let data = try? JSONSerialization.data(withJSONObject: json, options: []),
           let resp = String(data: data, encoding: .utf8) {
            return resp
        } else {
            return "{error: \"Unable to serialise response\"}"
        }
        
    }
}
