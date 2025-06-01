import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import "../"

Rectangle {
    id: button
    
    property string text: ""
    property string iconSource: ""
    property bool primary: false
    property bool enabled: true
    
    signal clicked()
    
    width: text ? Math.max(80, textItem.width + Style.spacing * 2) : Style.buttonHeight
    height: Style.buttonHeight
    radius: Style.borderRadius
    
    color: {
        if (!button.enabled) return Style.panelBackground
        if (mouseArea.pressed) return primary ? Style.buttonPressed : Style.buttonHover
        if (mouseArea.containsMouse) return primary ? Style.buttonHover : Style.lavenderDream
        return primary ? Style.accentTeal : Style.mintSoft
    }
    
    // Subtle shadow effect
    layer.enabled: true
    layer.effect: DropShadow {
        horizontalOffset: Style.shadowOffset
        verticalOffset: Style.shadowOffset
        radius: Style.shadowBlur
        samples: Style.shadowBlur * 2 + 1
        color: Style.shadowColor
        opacity: Style.shadowOpacity
    }
    
    // Smooth color transitions
    Behavior on color {
        ColorAnimation {
            duration: Style.animationFast
        }
    }
    
    // Content layout
    Row {
        anchors.centerIn: parent
        spacing: Style.spacingSmall
        
        // Icon (if provided)
        Image {
            id: iconItem
            visible: iconSource !== ""
            source: iconSource
            width: 20
            height: 20
            anchors.verticalCenter: parent.verticalCenter
            
            // Smooth icon color based on button state
            ColorOverlay {
                anchors.fill: iconItem
                source: iconItem
                color: button.primary ? Style.backgroundColor : Style.textPrimary
            }
        }
        
        // Text
        Text {
            id: textItem
            text: button.text
            visible: button.text !== ""
            font.family: Style.fontFamily
            font.pixelSize: Style.fontSizeBody
            font.weight: Style.fontWeightMedium
            color: button.primary ? Style.backgroundColor : Style.textPrimary
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    
    // Mouse interaction
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: button.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        
        onClicked: button.clicked()
    }
    
    // Subtle scale animation on press
    scale: mouseArea.pressed ? 0.98 : 1.0
    Behavior on scale {
        NumberAnimation {
            duration: Style.animationFast
        }
    }
}