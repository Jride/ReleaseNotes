//
//  WindowContentViewController.swift
//  AppKitPrompt
//
//  Created by Josh Rideout on 17/04/2023.
//

import Cocoa
import AppKit
import SwiftUI

class WindowContentViewController: NSViewController {
    
    private var viewContainer = NSBox(frame: .zero)
    private var onExit: (() -> Void)!
    private let padding: CGFloat = 10
    private let toolbarHeight: CGFloat = 28
    private let buttonHeight: CGFloat = 30
    private var header: NSTextField!
    private var link: NSTextView!
    private var confirmButton: NSButton!
    private var denyButton: NSButton!
    private var dismissAlertButton: NSButton!
    private var previousLayoutHeight: CGFloat = .zero
    private var contentHeight: CGFloat = .zero
    private let font = NSFont(name: "HelveticaNeue-Medium", size: 18)
    private let buttonFont = NSFont(name: "HelveticaNeue-Medium", size: 15)
    private let screenFrame = NSScreen.main!.frame
    
    convenience init(onExit: @escaping () -> Void) {
        self.init(nibName: nil, bundle: nil)
        self.onExit = onExit
    }
    
    override init(nibName nibNameOrNil: NSNib.Name?, bundle nibBundleOrNil: Bundle?) {
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    override func loadView() {
        addViewContainer()
        setupView()
    }
    
    override func viewDidAppear() {
        super.viewDidAppear()
    }
    
    override func viewDidLayout() {
        viewContainer.frame = view.bounds
    
        var yPos: CGFloat = view.bounds.height-padding
        let contentWidth = view.bounds.width-padding
        
        let headerHeight = header.height(forWidth: contentWidth)
        header.frame.size = CGSize(
            width: contentWidth,
            height: headerHeight
        )
        
        contentHeight = headerHeight + padding
        
        yPos -= headerHeight
        header.frame.origin = CGPoint(x: 0, y: yPos)
        
        if args.promptLink != nil {
            let linkHeight = link.height(forWidth: contentWidth)
            link.frame.size = CGSize(
                width: contentWidth,
                height: linkHeight
            )
            
            contentHeight += linkHeight + (padding*2)
            
            yPos -= linkHeight + padding
            link.frame.origin = CGPoint(x: 0, y: yPos)
            yPos -= padding
        }
        
        yPos -= padding/2
        yPos -= toolbarHeight
        
        let buttonWidth = (contentWidth/2) - padding/2
        
        dismissAlertButton.setFrameSize(.init(width: (contentWidth - padding), height: buttonHeight))
        dismissAlertButton.setFrameOrigin(.init(x: 0, y: yPos))
        
        confirmButton.setFrameSize(.init(width: buttonWidth, height: buttonHeight))
        confirmButton.setFrameOrigin(.init(x: 0, y: yPos))
        
        denyButton.setFrameSize(.init(width: buttonWidth, height: buttonHeight))
        denyButton.setFrameOrigin(.init(x: buttonWidth + padding/2, y: yPos))
        
        contentHeight += buttonHeight
        contentHeight += padding
        
        updateWindowFrameIfNeeded()
    }
    
    private func setupView() {
        
        header = NSTextField()
        header.frame = CGRect.zero
        header.stringValue = args.promptText
        header.preferredMaxLayoutWidth = view.bounds.width
        header.backgroundColor = .clear
        header.textColor = .white
        header.maximumNumberOfLines = 0
        header.alignment = .center
        header.font = font
        header.isBezeled = false
        header.isEditable = false
        header.sizeToFit()
        view.addSubview(header)
        
        setupLinkText()
        
        dismissAlertButton = NSButton(
            title: args.dismissAlertButtonCopy ?? "Dismiss",
            target: self,
            action: #selector(denyButtonAction)
        )
        dismissAlertButton.bezelStyle = .rounded
        dismissAlertButton.font = buttonFont
        view.addSubview(dismissAlertButton)
        
        confirmButton = NSButton(
            title: args.confirmButtonCopy,
            target: self,
            action: #selector(confirmButtonAction)
        )
        confirmButton.bezelStyle = .rounded
        confirmButton.font = buttonFont
        view.addSubview(confirmButton)
        
        denyButton = NSButton(
            title: args.denyButtonCopy,
            target: self,
            action: #selector(denyButtonAction)
        )
        denyButton.bezelStyle = .rounded
        denyButton.font = buttonFont
        view.addSubview(denyButton)
        
        if args.dismissAlertButtonCopy == nil {
            dismissAlertButton.isHidden = true
        } else {
            denyButton.isHidden = true
            confirmButton.isHidden = true
        }
    }
    
    private func setupLinkText() {
        guard let promptLink = args.promptLink else {
            return
        }
        
        let title = args.promptLinkTitle ?? promptLink
        
        let attributedString = NSMutableAttributedString(string: title)
        let linkRange = NSRange(location: 0, length: attributedString.length)
        attributedString.addAttribute(.link, value: promptLink, range: linkRange)
        
        link = NSTextView()
        link.frame = .zero
        link.backgroundColor = .clear
        link.textColor = .systemBlue
        link.textStorage?.setAttributedString(attributedString)
        link.alignment = .center
        link.font = NSFont(name: "HelveticaNeue", size: 17)
        link.isEditable = false
        link.isSelectable = true
        link.sizeToFit()
        view.addSubview(link)
    }
    
    private func addViewContainer() {
        viewContainer.boxType = .custom
        viewContainer.borderWidth = 0
        viewContainer.alphaValue = 1
        view = viewContainer
    }
    
    @objc private func confirmButtonAction() {
        response.promptResponse = true
        onExit()
    }
    
    @objc private func denyButtonAction() {
        response.promptResponse = false
        onExit()
    }
    
    func updateWindowFrameIfNeeded() {
        guard contentHeight != previousLayoutHeight else {
            return
        }
        
        previousLayoutHeight = contentHeight
        
        var viewFrame = viewContainer.frame
        viewFrame.size.height = contentHeight
        viewContainer.frame = viewFrame
        
        guard let window = view.window else { return }
        viewFrame.size.height += toolbarHeight
        var windowOrigin = window.frame.origin
        windowOrigin.y = screenFrame.midY - viewFrame.height/2
        window.setFrame(.init(
            origin: windowOrigin,
            size: viewFrame.size
        ), display: true, animate: false)
    }
    
}

extension NSTextField {
    
    func height(forWidth width: CGFloat) -> CGFloat {
        guard let font else { return .zero }
        
        let constrainedSize = CGSize(width: width, height: .greatestFiniteMagnitude)
        let rect = (stringValue as NSString)
            .boundingRect(with: constrainedSize,
                          options: [.usesLineFragmentOrigin, .usesFontLeading],
                          attributes: [NSAttributedString.Key.font: font], context: nil)
        return rect.height
    }
}

extension NSTextView {
    
    func height(forWidth width: CGFloat) -> CGFloat {
        guard let font, let textStorage else { return .zero }
        
        let constrainedSize = CGSize(width: width, height: .greatestFiniteMagnitude)
        let rect = textStorage.string.boundingRect(with: constrainedSize,
                          options: [.usesLineFragmentOrigin, .usesFontLeading],
                          attributes: [NSAttributedString.Key.font: font], context: nil)
        return rect.height
    }
}
