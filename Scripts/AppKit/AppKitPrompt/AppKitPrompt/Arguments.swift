//
//  Arguments.swift
//  AppKitPrompt
//
//  Created by Josh Rideout on 18/04/2023.
//

import Foundation

/*
 {
   "promptTitle": "Prompt Title Goes Here",
   "promptText": "This is where you put your yes or no question",
   "promptLink": "http://www.google.com",
   "promptLinkTitle": "Click me",
   "confirmButtonCopy": "Confirm",
   "denyButtonCopy": "Deny",
   "dismissAlertButtonCopy": "Ok" // Only shows one action button
 }
 */

struct Arguments {
    let promptTitle: String
    let promptText: String
    let promptLink: String?
    let promptLinkTitle: String?
    let dismissAlertButtonCopy: String?
    let confirmButtonCopy: String
    let denyButtonCopy: String
    
    static func decodeCommandLine() -> Arguments {
        
        response.logs.append("Command Line Arguments")
        response.logs.append(CommandLine.arguments.joined(separator: " - "))
        
        guard
            CommandLine.arguments.count >= 2,
            let data = CommandLine.arguments[1].data(using: .utf8),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: String] else {
            response.logs.append("Failed to decode JSON from input arguments")
            return Arguments(
                promptTitle: "Prompt",
                promptText: "Yes or No?",
                promptLink: nil,
                promptLinkTitle: nil,
                dismissAlertButtonCopy: nil,
                confirmButtonCopy: "Yes",
                denyButtonCopy: "No"
            )
        }
         
        return Arguments(
            promptTitle: json["promptTitle"] ?? "Prompt",
            promptText: json["promptText"] ?? "Yes or No?",
            promptLink: json["promptLink"],
            promptLinkTitle: json["promptLinkTitle"],
            dismissAlertButtonCopy: json["dismissAlertButtonCopy"],
            confirmButtonCopy: json["confirmButtonCopy"] ?? "Yes",
            denyButtonCopy: json["denyButtonCopy"] ?? "No"
        )
    }
}
