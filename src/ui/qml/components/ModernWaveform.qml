import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import "../"

Rectangle {
    id: waveform
    
    property var audioData: null      // Audio samples array
    property real duration: 0.0       // Total duration in seconds
    property real position: 0.0       // Current playback position
    property real zoomLevel: 1.0      // Zoom level (1.0 = full view)
    property real scrollPosition: 0.0 // Scroll position in seconds
    
    signal seekRequested(real position)
    
    color: Style.backgroundColor
    radius: Style.borderRadius
    
    // Subtle border
    border.width: 1
    border.color: Style.panelBackground
    
    // Main content area
    Item {
        id: contentArea
        anchors.fill: parent
        anchors.margins: Style.spacing
        clip: true
        
        // Background grid for time reference
        Canvas {
            id: gridCanvas
            anchors.fill: parent
            
            onPaint: {
                if (waveform.duration <= 0) return
                
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                
                // Grid styling
                ctx.strokeStyle = Style.panelBackground
                ctx.lineWidth = 1
                ctx.setLineDash([2, 4])
                
                // Calculate time intervals
                var visibleDuration = waveform.duration / waveform.zoomLevel
                var pixelsPerSecond = width / visibleDuration
                var interval = getTimeInterval(pixelsPerSecond)
                
                // Draw vertical grid lines
                var startTime = Math.ceil(waveform.scrollPosition / interval) * interval
                var endTime = waveform.scrollPosition + visibleDuration
                
                for (var time = startTime; time <= endTime; time += interval) {
                    var x = timeToX(time)
                    if (x >= 0 && x <= width) {
                        ctx.beginPath()
                        ctx.moveTo(x, 0)
                        ctx.lineTo(x, height)
                        ctx.stroke()
                    }
                }
            }
            
            function getTimeInterval(pixelsPerSecond) {
                if (pixelsPerSecond > 100) return 1.0      // 1 second
                if (pixelsPerSecond > 50) return 2.0       // 2 seconds
                if (pixelsPerSecond > 20) return 5.0       // 5 seconds
                if (pixelsPerSecond > 10) return 10.0      // 10 seconds
                return 30.0                                // 30 seconds
            }
            
            function timeToX(time) {
                var visibleDuration = waveform.duration / waveform.zoomLevel
                var relativeTime = time - waveform.scrollPosition
                return (relativeTime / visibleDuration) * width
            }
        }
        
        // Waveform visualization
        Canvas {
            id: waveformCanvas
            anchors.fill: parent
            
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                
                if (!waveform.audioData || waveform.audioData.length === 0) {
                    drawPlaceholder(ctx)
                    return
                }
                
                drawWaveform(ctx)
            }
            
            function drawPlaceholder(ctx) {
                ctx.fillStyle = Style.textTertiary
                ctx.font = Style.fontSizeBody + "px " + Style.fontFamily
                ctx.textAlign = "center"
                ctx.fillText("טען קובץ אודיו כדי לראות את הוויזואליזציה", width / 2, height / 2)
            }
            
            function drawWaveform(ctx) {
                var centerY = height / 2
                var amplitude = height * 0.4
                
                // Calculate visible data range
                var visibleDuration = waveform.duration / waveform.zoomLevel
                var startTime = waveform.scrollPosition
                var endTime = Math.min(startTime + visibleDuration, waveform.duration)
                
                var sampleRate = waveform.audioData.length / waveform.duration
                var startSample = Math.floor(startTime * sampleRate)
                var endSample = Math.floor(endTime * sampleRate)
                
                if (startSample >= waveform.audioData.length) return
                
                endSample = Math.min(endSample, waveform.audioData.length)
                var visibleData = waveform.audioData.slice(startSample, endSample)
                
                if (visibleData.length === 0) return
                
                // Create gradient for waveform
                var gradient = ctx.createLinearGradient(0, 0, 0, height)
                gradient.addColorStop(0, Style.skyBlue)
                gradient.addColorStop(0.5, Style.waveformAccent)
                gradient.addColorStop(1, Style.skyBlue)
                
                ctx.fillStyle = gradient
                ctx.strokeStyle = Style.accentTeal
                ctx.lineWidth = 1
                
                // Downsample for display if needed
                var samplesPerPixel = visibleData.length / width
                
                if (samplesPerPixel > 1) {
                    drawEnvelopeWaveform(ctx, visibleData, centerY, amplitude, samplesPerPixel)
                } else {
                    drawDetailedWaveform(ctx, visibleData, centerY, amplitude)
                }
            }
            
            function drawEnvelopeWaveform(ctx, data, centerY, amplitude, samplesPerPixel) {
                ctx.beginPath()
                
                for (var x = 0; x < width; x++) {
                    var startIdx = Math.floor(x * samplesPerPixel)
                    var endIdx = Math.floor((x + 1) * samplesPerPixel)
                    endIdx = Math.min(endIdx, data.length)
                    
                    if (startIdx < data.length) {
                        var chunk = data.slice(startIdx, endIdx)
                        var minVal = Math.min(...chunk)
                        var maxVal = Math.max(...chunk)
                        
                        var minY = centerY + minVal * amplitude
                        var maxY = centerY + maxVal * amplitude
                        
                        // Draw vertical line for this pixel
                        ctx.moveTo(x, minY)
                        ctx.lineTo(x, maxY)
                    }
                }
                
                ctx.stroke()
            }
            
            function drawDetailedWaveform(ctx, data, centerY, amplitude) {
                ctx.beginPath()
                
                for (var i = 0; i < data.length && i < width; i++) {
                    var x = (i / data.length) * width
                    var y = centerY + data[i] * amplitude
                    
                    if (i === 0) {
                        ctx.moveTo(x, y)
                    } else {
                        ctx.lineTo(x, y)
                    }
                }
                
                ctx.stroke()
            }
        }
        
        // Playhead indicator
        Rectangle {
            id: playhead
            visible: waveform.duration > 0
            x: timeToX(waveform.position)
            width: Style.playheadWidth
            height: parent.height
            color: Style.playheadColor
            radius: width / 2
            
            // Subtle glow effect
            layer.enabled: true
            layer.effect: DropShadow {
                horizontalOffset: 0
                verticalOffset: 0
                radius: 8
                samples: 17
                color: Style.playheadColor
                opacity: 0.4
            }
            
            // Smooth position animation
            Behavior on x {
                NumberAnimation {
                    duration: mouseArea.pressed ? 0 : Style.animationFast
                }
            }
            
            function timeToX(time) {
                if (waveform.duration <= 0) return 0
                var visibleDuration = waveform.duration / waveform.zoomLevel
                var relativeTime = time - waveform.scrollPosition
                return (relativeTime / visibleDuration) * contentArea.width
            }
        }
        
        // Current time indicator at playhead
        Rectangle {
            visible: playhead.visible && playhead.x >= 0 && playhead.x <= parent.width
            x: Math.max(0, Math.min(parent.width - width, playhead.x - width / 2))
            y: -height - Style.spacingSmall
            width: timeText.width + Style.spacingSmall * 2
            height: timeText.height + Style.spacingSmall
            color: Style.playheadColor
            radius: Style.borderRadiusSmall
            
            Text {
                id: timeText
                anchors.centerIn: parent
                text: formatTime(waveform.position)
                font.family: Style.fontFamilyMono
                font.pixelSize: Style.fontSizeCaption
                font.weight: Style.fontWeightMedium
                color: Style.backgroundColor
            }
        }
    }
    
    // Mouse interaction for seeking
    MouseArea {
        id: mouseArea
        anchors.fill: contentArea
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        
        onClicked: {
            var timeAtClick = xToTime(mouse.x)
            if (timeAtClick >= 0 && timeAtClick <= waveform.duration) {
                waveform.seekRequested(timeAtClick)
            }
        }
        
        function xToTime(x) {
            if (waveform.duration <= 0) return 0
            var visibleDuration = waveform.duration / waveform.zoomLevel
            var relativeTime = (x / contentArea.width) * visibleDuration
            return waveform.scrollPosition + relativeTime
        }
    }
    
    // Mouse position indicator
    Rectangle {
        visible: mouseArea.containsMouse && !mouseArea.pressed
        x: mouseArea.mouseX
        width: 2
        height: contentArea.height
        color: Style.textTertiary
        opacity: 0.6
        
        Rectangle {
            x: -timeAtMouseText.width / 2
            y: -height - Style.spacingSmall
            width: timeAtMouseText.width + Style.spacingSmall
            height: timeAtMouseText.height + Style.spacingSmall / 2
            color: Style.textSecondary
            radius: Style.borderRadiusSmall
            
            Text {
                id: timeAtMouseText
                anchors.centerIn: parent
                text: formatTime(mouseArea.xToTime(mouseArea.mouseX))
                font.family: Style.fontFamilyMono
                font.pixelSize: Style.fontSizeSmall
                color: Style.backgroundColor
            }
        }
    }
    
    // Zoom and scroll controls
    Item {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: Style.spacingSmall
        width: zoomControls.width
        height: zoomControls.height
        
        Row {
            id: zoomControls
            spacing: Style.spacingSmall
            
            ModernButton {
                text: "−"
                width: 32
                height: 32
                onClicked: zoomOut()
            }
            
            ModernButton {
                text: "+"
                width: 32
                height: 32
                onClicked: zoomIn()
            }
            
            ModernButton {
                text: "⟲"
                width: 32
                height: 32
                onClicked: resetZoom()
            }
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
    
    function setAudioData(data, sampleRate) {
        waveform.audioData = data
        waveform.duration = data ? data.length / sampleRate : 0
        gridCanvas.requestPaint()
        waveformCanvas.requestPaint()
    }
    
    function setPosition(newPosition) {
        waveform.position = newPosition
        
        // Auto-scroll to keep playhead visible
        var visibleDuration = waveform.duration / waveform.zoomLevel
        if (newPosition < waveform.scrollPosition || 
            newPosition > waveform.scrollPosition + visibleDuration) {
            waveform.scrollPosition = Math.max(0, newPosition - visibleDuration / 2)
            gridCanvas.requestPaint()
            waveformCanvas.requestPaint()
        }
    }
    
    function zoomIn() {
        waveform.zoomLevel = Math.min(10.0, waveform.zoomLevel * 1.5)
        gridCanvas.requestPaint()
        waveformCanvas.requestPaint()
    }
    
    function zoomOut() {
        waveform.zoomLevel = Math.max(0.1, waveform.zoomLevel / 1.5)
        gridCanvas.requestPaint()
        waveformCanvas.requestPaint()
    }
    
    function resetZoom() {
        waveform.zoomLevel = 1.0
        waveform.scrollPosition = 0.0
        gridCanvas.requestPaint()
        waveformCanvas.requestPaint()
    }
}