# Bina Cshera (בינה כשרה) - HolyPlayer Pro

A sophisticated audio player application with synchronized transcript display and waveform visualization, built with Python/PySide6 and packaged as a self-contained Windows executable.

## Features

- **Advanced Audio Playback**: Support for MP3, WAV, FLAC, and other common audio formats
- **Waveform Visualization**: Real-time waveform display with synchronized playhead
- **Transcript Synchronization**: Display and sync text transcripts with audio playback
- **Modern GUI**: Clean, intuitive interface built with PySide6
- **Self-Contained**: Single executable file requiring no external installations

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Engine Layer**: Core audio processing and file handling
- **Controllers**: Business logic and coordination between UI and engine
- **UI Layer**: PySide6-based graphical interface with custom widgets
- **Utils**: Common utilities and helper functions

## Development Environment

This project uses GitHub Codespaces with a custom devcontainer for consistent development:

- Python 3.12 with PySide6
- FFmpeg static binaries for audio processing
- VNC desktop environment for GUI development
- Automated Windows build pipeline

## Getting Started

### Development Setup

1. Open in GitHub Codespaces
2. The devcontainer will automatically set up the development environment
3. Access the VNC desktop at the forwarded port 6080
4. Run the application: `python src/__main__.py`

### Building Windows Executable

The project includes GitHub Actions workflow for automated Windows builds:

1. Push to `main` branch or trigger manually
2. Download the built executable from GitHub Actions artifacts
3. The executable includes all dependencies and FFmpeg binary

## Project Structure

