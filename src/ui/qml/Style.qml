pragma Singleton
import QtQuick 2.15

QtObject {
    id: style
    
    // Color Palette - Soft Pastels for 2025
    readonly property color backgroundColor: "#FAF7F0"        // Warm off-white (Almond cream)
    readonly property color secondaryBackground: "#F5F5F7"   // Light neutral cloud
    readonly property color panelBackground: "#EAE6F0"       // Light lavender-gray
    
    // Soft Pastel Colors
    readonly property color mintSoft: "#CFF0E8"              // Soft mint for content backgrounds
    readonly property color peachLight: "#FFE5D4"           // Light peach for highlights
    readonly property color lavenderDream: "#E0D6F5"        // Dreamy lavender for interactive elements
    readonly property color skyBlue: "#D1E8FF"              // Sky blue for waveform/visual elements
    
    // Accent Colors - Slightly more saturated but still soft
    readonly property color accentTeal: "#7DD8C9"           // Primary accent (buttons, playhead)
    readonly property color accentCoral: "#FFADAD"          // Secondary accent (alerts, errors)
    
    // Text Colors
    readonly property color textPrimary: "#333740"          // Very dark gray (not pure black)
    readonly property color textSecondary: "#6C757D"        // Medium gray for labels
    readonly property color textTertiary: "#9CA3AF"         // Light gray for subtle text
    
    // Interactive States
    readonly property color buttonHover: "#B8E6DE"          // Lighter teal for hover
    readonly property color buttonPressed: "#5FCAB0"        // Darker teal for pressed
    
    // Dark Mode Variants (Soft Dark)
    readonly property color darkBackground: "#3E4C5E"       // Blue-gray dark
    readonly property color darkPanel: "#4B4264"            // Purple-ink dark
    readonly property color darkTextPrimary: "#F8F9FA"     // Off-white text
    
    // Dimensions & Spacing
    readonly property int borderRadius: 12                   // Standard border radius
    readonly property int borderRadiusSmall: 8              // Small border radius
    readonly property int borderRadiusLarge: 16             // Large border radius
    
    readonly property int spacing: 16                        // Standard spacing
    readonly property int spacingSmall: 8                   // Small spacing
    readonly property int spacingLarge: 24                  // Large spacing
    readonly property int spacingXLarge: 32                 // Extra large spacing
    
    // Typography
    readonly property string fontFamily: "Inter"            // Primary font
    readonly property string fontFamilyMono: "JetBrains Mono" // Monospace font
    
    readonly property int fontSizeHeading: 22               // Main headings
    readonly property int fontSizeSubheading: 18            // Sub headings
    readonly property int fontSizeBody: 14                  // Body text
    readonly property int fontSizeCaption: 12               // Captions and labels
    readonly property int fontSizeSmall: 10                 // Small text
    
    readonly property int fontWeightLight: 300
    readonly property int fontWeightRegular: 400
    readonly property int fontWeightMedium: 500
    readonly property int fontWeightSemiBold: 600
    readonly property int fontWeightBold: 700
    
    // Component Dimensions
    readonly property int buttonHeight: 44                  // Standard button height
    readonly property int buttonHeightSmall: 36             // Small button height
    readonly property int buttonHeightLarge: 52             // Large button height
    
    readonly property int controlsBarHeight: 80             // Audio controls bar height
    readonly property int seekBarHeight: 8                  // Seek bar thickness
    readonly property int thumbSize: 20                     // Slider thumb size
    
    // Shadows & Effects
    readonly property color shadowColor: "#000000"
    readonly property real shadowOpacity: 0.08             // Very subtle shadows
    readonly property int shadowBlur: 16
    readonly property int shadowOffset: 2
    
    // Animation Durations
    readonly property int animationFast: 150               // Fast transitions
    readonly property int animationNormal: 250             // Normal transitions
    readonly property int animationSlow: 400               // Slow transitions
    
    // Waveform Visualization
    readonly property color waveformColor: skyBlue
    readonly property color waveformAccent: accentTeal
    readonly property color playheadColor: accentTeal
    readonly property int playheadWidth: 3
    
    // Speaker Diarization Colors
    readonly property var speakerColors: [
        mintSoft,
        peachLight,
        lavenderDream,
        skyBlue,
        "#F0C4DE",  // Soft pink
        "#C7E9B0",  // Light green
        "#FFE4B5",  // Moccasin
        "#E6E6FA"   // Lavender
    ]
    
    function getSpeakerColor(speakerIndex) {
        return speakerColors[speakerIndex % speakerColors.length]
    }
    
    // Theme Management
    property bool isDarkMode: false
    
    function getBackgroundColor() {
        return isDarkMode ? darkBackground : backgroundColor
    }
    
    function getTextColor() {
        return isDarkMode ? darkTextPrimary : textPrimary
    }
    
    function getPanelColor() {
        return isDarkMode ? darkPanel : panelBackground
    }
}