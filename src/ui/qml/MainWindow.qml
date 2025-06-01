import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15
import "components"

ApplicationWindow {
    id: mainWindow
    
    title: "נגן בינה כשרה"
    width: 1200
    height: 800
    minimumWidth: 800
    minimumHeight: 600
    
    flags: Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
    
    // Properties for audio control integration
    property alias waveform: waveformDisplay
    property alias seekBar: audioSeekBar
    property alias playButton: playBtn
    property alias pauseButton: pauseBtn
    property alias stopButton: stopBtn
    
    // Background with subtle gradient
    Rectangle {
        anchors.fill: parent
        color: Style.backgroundColor
        
        // Subtle background pattern
        Rectangle {
            anchors.fill: parent
            opacity: 0.02
            
            Canvas {
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.strokeStyle = Style.textSecondary
                    ctx.lineWidth = 1
                    
                    // Draw subtle dot pattern
                    for (var x = 0; x < width; x += 20) {
                        for (var y = 0; y < height; y += 20) {
                            ctx.beginPath()
                            ctx.arc(x, y, 1, 0, 2 * Math.PI)
                            ctx.stroke()
                        }
                    }
                }
            }
        }
    }
    
    // Main content layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.spacing
        spacing: Style.spacing
        
        // Header section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: Style.panelBackground
            radius: Style.borderRadius
            
            // Subtle shadow
            layer.enabled: true
            layer.effect: DropShadow {
                horizontalOffset: 0
                verticalOffset: 2
                radius: 8
                samples: 17
                color: Style.shadowColor
                opacity: Style.shadowOpacity
            }
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: Style.spacing
                
                // App icon and title
                Row {
                    spacing: Style.spacingSmall
                    
                    Rectangle {
                        width: 32
                        height: 32
                        radius: Style.borderRadiusSmall
                        color: Style.accentTeal
                        
                        Text {
                            anchors.centerIn: parent
                            text: "🎵"
                            font.pixelSize: 18
                        }
                    }
                    
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Text {
                            text: "נגן בינה כשרה"
                            font.family: Style.fontFamily
                            font.pixelSize: Style.fontSizeSubheading
                            font.weight: Style.fontWeightSemiBold
                            color: Style.textPrimary
                        }
                        
                        Text {
                            id: fileNameLabel
                            text: "לא נטען קובץ"
                            font.family: Style.fontFamily
                            font.pixelSize: Style.fontSizeCaption
                            color: Style.textSecondary
                        }
                    }
                }
                
                // Spacer
                Item {
                    Layout.fillWidth: true
                }
                
                // Menu buttons
                Row {
                    spacing: Style.spacingSmall
                    
                    ModernButton {
                        text: "פתח קובץ"
                        primary: true
                        onClicked: openFileDialog()
                    }
                    
                    ModernButton {
                        text: "⚙️"
                        width: Style.buttonHeight
                        onClicked: showSettings()
                    }
                }
            }
        }
        
        // Content area
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Style.backgroundColor
            radius: Style.borderRadius
            border.width: 1
            border.color: Style.panelBackground
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: Style.spacing
                spacing: Style.spacing
                
                // Main visualization area
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Style.mintSoft
                    radius: Style.borderRadius
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Style.spacing
                        spacing: Style.spacing
                        
                        // Waveform display
                        ModernWaveform {
                            id: waveformDisplay
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            
                            onSeekRequested: function(position) {
                                // Will be connected to audio engine
                                console.log("Seek requested:", position)
                            }
                        }
                        
                        // Audio controls
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Style.controlsBarHeight
                            color: Style.backgroundColor
                            radius: Style.borderRadius
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: Style.spacingSmall
                                spacing: Style.spacingSmall
                                
                                // Transport controls
                                RowLayout {
                                    Layout.fillWidth: true
                                    
                                    ModernButton {
                                        id: playBtn
                                        text: "▶️"
                                        primary: true
                                        enabled: false
                                        onClicked: playAudio()
                                    }
                                    
                                    ModernButton {
                                        id: pauseBtn
                                        text: "⏸️"
                                        enabled: false
                                        onClicked: pauseAudio()
                                    }
                                    
                                    ModernButton {
                                        id: stopBtn
                                        text: "⏹️"
                                        enabled: false
                                        onClicked: stopAudio()
                                    }
                                    
                                    // Spacer
                                    Item {
                                        Layout.fillWidth: true
                                    }
                                    
                                    // Volume control
                                    Text {
                                        text: "עוצמה:"
                                        font.family: Style.fontFamily
                                        font.pixelSize: Style.fontSizeBody
                                        color: Style.textSecondary
                                    }
                                    
                                    Rectangle {
                                        width: 100
                                        height: 20
                                        color: Style.panelBackground
                                        radius: height / 2
                                        
                                        Rectangle {
                                            width: parent.width * 0.7 // 70% volume
                                            height: parent.height
                                            color: Style.accentTeal
                                            radius: height / 2
                                        }
                                    }
                                }
                                
                                // Seek bar
                                ModernSeekBar {
                                    id: audioSeekBar
                                    Layout.fillWidth: true
                                    
                                    onSeekRequested: function(position) {
                                        // Will be connected to audio engine
                                        console.log("Seek requested from bar:", position)
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Transcript panel
                Rectangle {
                    Layout.preferredWidth: 350
                    Layout.fillHeight: true
                    color: Style.peachLight
                    radius: Style.borderRadius
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Style.spacing
                        spacing: Style.spacing
                        
                        // Transcript header
                        RowLayout {
                            Layout.fillWidth: true
                            
                            Text {
                                text: "תמלול"
                                font.family: Style.fontFamily
                                font.pixelSize: Style.fontSizeSubheading
                                font.weight: Style.fontWeightSemiBold
                                color: Style.textPrimary
                            }
                            
                            Item {
                                Layout.fillWidth: true
                            }
                            
                            Text {
                                id: segmentCountLabel
                                text: "0 קטעים"
                                font.family: Style.fontFamily
                                font.pixelSize: Style.fontSizeCaption
                                color: Style.textSecondary
                            }
                        }
                        
                        // Search box
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            color: Style.backgroundColor
                            radius: Style.borderRadiusSmall
                            border.width: 1
                            border.color: Style.panelBackground
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: Style.spacingSmall
                                
                                Text {
                                    text: "🔍"
                                    color: Style.textTertiary
                                }
                                
                                TextInput {
                                    Layout.fillWidth: true
                                    font.family: Style.fontFamily
                                    font.pixelSize: Style.fontSizeBody
                                    color: Style.textPrimary
                                    
                                    Text {
                                        anchors.fill: parent
                                        text: "חיפוש בתמלול..."
                                        color: Style.textTertiary
                                        visible: parent.text === ""
                                    }
                                }
                            }
                        }
                        
                        // Transcript content
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            
                            ScrollBar.vertical.policy: ScrollBar.AsNeeded
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            
                            ColumnLayout {
                                width: parent.width
                                spacing: Style.spacingSmall
                                
                                // Placeholder content
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 200
                                    color: Style.backgroundColor
                                    radius: Style.borderRadiusSmall
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "אין תמלול זמין.\n\nטען קובץ אודיו עם קובץ תמלול נלווה."
                                        font.family: Style.fontFamily
                                        font.pixelSize: Style.fontSizeBody
                                        color: Style.textTertiary
                                        horizontalAlignment: Text.AlignHCenter
                                        wrapMode: Text.WordWrap
                                    }
                                }
                                
                                // Future transcript segments will be added here dynamically
                            }
                        }
                    }
                }
            }
        }
        
        // Status bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            color: Style.panelBackground
            radius: Style.borderRadiusSmall
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: Style.spacingSmall
                
                Text {
                    id: statusLabel
                    text: "מוכן"
                    font.family: Style.fontFamily
                    font.pixelSize: Style.fontSizeCaption
                    color: Style.textSecondary
                }
                
                Item {
                    Layout.fillWidth: true
                }
                
                Text {
                    text: "נגן בינה כשרה v1.0"
                    font.family: Style.fontFamily
                    font.pixelSize: Style.fontSizeCaption
                    color: Style.textTertiary
                }
            }
        }
    }
    
    // Functions that will be connected to the audio engine
    function openFileDialog() {
        statusLabel.text = "פותח תיבת דו-שיח לבחירת קובץ..."
        // This will be connected to Python backend
    }
    
    function playAudio() {
        statusLabel.text = "מנגן..."
        // This will be connected to Python backend
    }
    
    function pauseAudio() {
        statusLabel.text = "מושהה"
        // This will be connected to Python backend
    }
    
    function stopAudio() {
        statusLabel.text = "עצר"
        // This will be connected to Python backend
    }
    
    function showSettings() {
        statusLabel.text = "פותח הגדרות..."
        // Future settings dialog
    }
    
    function updateFileName(fileName) {
        fileNameLabel.text = fileName
    }
    
    function updateStatus(status) {
        statusLabel.text = status
    }
    
    function setAudioData(data, sampleRate) {
        waveformDisplay.setAudioData(data, sampleRate)
    }
    
    function setPosition(position) {
        waveformDisplay.setPosition(position)
        audioSeekBar.setPosition(position)
    }
    
    function setDuration(duration) {
        audioSeekBar.setDuration(duration)
    }
    
    function enableControls(enabled) {
        playBtn.enabled = enabled
        pauseBtn.enabled = enabled
        stopBtn.enabled = enabled
    }
}