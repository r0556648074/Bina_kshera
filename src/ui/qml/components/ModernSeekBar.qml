import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import "../"

Item {
    id: seekBar
    
    property real value: 0.0          // Current position (0.0 to 1.0)
    property real duration: 0.0       // Total duration in seconds
    property real position: 0.0       // Current position in seconds
    property bool seeking: false      // Whether user is currently seeking
    
    signal seekRequested(real position)
    
    height: Style.seekBarHeight + Style.thumbSize
    
    // Background track
    Rectangle {
        id: track
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height: Style.seekBarHeight
        radius: height / 2
        color: Style.panelBackground
        
        // Subtle inner shadow for depth
        layer.enabled: true
        layer.effect: InnerShadow {
            horizontalOffset: 0
            verticalOffset: 1
            radius: 2
            samples: 5
            color: Style.shadowColor
            opacity: 0.1
        }
    }
    
    // Progress track
    Rectangle {
        id: progressTrack
        anchors.left: track.left
        anchors.verticalCenter: track.verticalCenter
        width: track.width * seekBar.value
        height: track.height
        radius: height / 2
        
        // Beautiful gradient from teal to slightly lighter teal
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: Style.accentTeal
            }
            GradientStop {
                position: 1.0
                color: Style.buttonHover
            }
        }
        
        // Smooth width animation
        Behavior on width {
            NumberAnimation {
                duration: seeking ? 0 : Style.animationFast
            }
        }
    }
    
    // Playhead thumb
    Rectangle {
        id: thumb
        x: (track.width - width) * seekBar.value
        anchors.verticalCenter: track.verticalCenter
        width: Style.thumbSize
        height: Style.thumbSize
        radius: width / 2
        color: Style.accentTeal
        border.width: 3
        border.color: Style.backgroundColor
        
        // Subtle glow effect
        layer.enabled: true
        layer.effect: DropShadow {
            horizontalOffset: 0
            verticalOffset: 2
            radius: 8
            samples: 17
            color: Style.accentTeal
            opacity: 0.3
        }
        
        // Scale up on hover/press
        scale: mouseArea.pressed ? 1.2 : (mouseArea.containsMouse ? 1.1 : 1.0)
        
        Behavior on scale {
            NumberAnimation {
                duration: Style.animationFast
            }
        }
        
        Behavior on x {
            NumberAnimation {
                duration: seeking ? 0 : Style.animationFast
            }
        }
    }
    
    // Mouse interaction
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        
        onPressed: {
            seeking = true
            updatePosition(mouse.x)
        }
        
        onPositionChanged: {
            if (pressed) {
                updatePosition(mouse.x)
            }
        }
        
        onReleased: {
            seeking = false
        }
        
        function updatePosition(mouseX) {
            var newValue = Math.max(0.0, Math.min(1.0, mouseX / track.width))
            seekBar.value = newValue
            var newPosition = newValue * seekBar.duration
            seekBar.seekRequested(newPosition)
        }
    }
    
    // Time labels
    Row {
        anchors.top: track.bottom
        anchors.topMargin: Style.spacingSmall
        anchors.left: parent.left
        anchors.right: parent.right
        
        Text {
            id: currentTimeLabel
            text: formatTime(seekBar.position)
            font.family: Style.fontFamilyMono
            font.pixelSize: Style.fontSizeCaption
            color: Style.textSecondary
        }
        
        Item {
            width: parent.width - currentTimeLabel.width - totalTimeLabel.width
        }
        
        Text {
            id: totalTimeLabel
            text: formatTime(seekBar.duration)
            font.family: Style.fontFamilyMono
            font.pixelSize: Style.fontSizeCaption
            color: Style.textSecondary
        }
    }
    
    function formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return "00:00"
        
        var hours = Math.floor(seconds / 3600)
        var minutes = Math.floor((seconds % 3600) / 60)
        var secs = Math.floor(seconds % 60)
        
        if (hours > 0) {
            return Qt.formatTime(new Date(0, 0, 0, hours, minutes, secs), "hh:mm:ss")
        } else {
            return Qt.formatTime(new Date(0, 0, 0, 0, minutes, secs), "mm:ss")
        }
    }
    
    function setPosition(newPosition) {
        if (!seeking) {
            seekBar.position = newPosition
            if (seekBar.duration > 0) {
                seekBar.value = newPosition / seekBar.duration
            }
        }
    }
    
    function setDuration(newDuration) {
        seekBar.duration = newDuration
        if (seekBar.duration > 0) {
            seekBar.value = seekBar.position / seekBar.duration
        }
    }
}