//
//  Response.swift
//  AppKitPrompt
//
//  Created by Josh Rideout on 17/04/2023.
//

import Foundation

struct Response {
    var errorMessage: String? = nil
    var promptResponse: Bool = false
    var logs = [String]()
    
    var jsonString: String {
        
        var json = [String: Any]()
        
        if let err = errorMessage {
            json["error"] = err
        }
        
        json["promptResponse"] = promptResponse.description.lowercased()
        json["logs"] = logs
        
        if let data = try? JSONSerialization.data(withJSONObject: json, options: []),
           let resp = String(data: data, encoding: .utf8) {
            return resp
        } else {
            return "{error: \"Unable to serialise response\"}"
        }
        
    }
}
