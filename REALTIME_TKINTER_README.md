# Realtime Voice Cloning - Tkinter GUI

A standalone tkinter-based GUI application for realtime voice cloning using RVC (Retrieval-Based Voice Conversion).

## Features

- **Model Loading**: Browse and load `.pth` model files with automatic model information display
- **Index File Support**: Optional `.index` file loading for improved voice quality
- **Audio Device Selection**: Easy selection of input/output audio devices with automatic detection
- **Realtime Processing**: Low-latency voice conversion with configurable parameters
- **Comprehensive Settings**:
  - Pitch shifting (-24 to +24 semitones)
  - Search feature ratio (index rate)
  - Volume envelope control
  - Voiceless consonant protection
  - Multiple F0 extraction methods (RMVPE, FCPE, SWIFT)
  - Embedder model selection
  - Autotune with adjustable strength
  - Performance tuning (chunk size, crossfade, etc.)
- **Real-time Monitoring**: Live latency display and status updates
- **Logging**: Built-in log viewer for debugging and monitoring

## Requirements

All dependencies are already included in the main project's `requirements.txt`. The application uses:
- tkinter (included with Python)
- torch
- sounddevice
- librosa
- numpy
- faiss

## Usage

### Running the Application

```bash
python realtime_tkinter.py
```

### Step-by-Step Guide

1. **Load a Model**:
   - Go to the "Model" tab
   - Click "Browse" next to "Model File (.pth)"
   - Select your trained RVC model file
   - Model information will be displayed automatically

2. **Load Index File (Optional)**:
   - Click "Browse" next to "Index File (.index)"
   - Select the corresponding index file for better quality
   - You can clear the index file selection if needed

3. **Configure Audio Devices**:
   - Go to the "Audio Devices" tab
   - Click "Refresh Devices" to scan for audio devices
   - Select your microphone/input device
   - Select your output device (e.g., virtual audio cable, speakers)
   - Adjust input/output gain as needed (default: 100%)
   - Enable VAD (Voice Activity Detection) to save CPU when not speaking
   - Enable Exclusive Mode for lower latency (WASAPI only)

4. **Adjust Voice Settings**:
   - Go to the "Voice Settings" tab
   - Adjust pitch shift (0 = no change)
   - Set search feature ratio (higher = more index influence)
   - Configure volume envelope and consonant protection
   - Select F0 extraction method:
     - **SWIFT**: Fastest, recommended for realtime
     - **RMVPE**: Balanced quality and speed
     - **FCPE**: High quality, slower
   - Choose embedder model (contentvec is default)
   - Enable autotune if needed (useful for singing)
   - Tune performance settings:
     - Lower chunk size = lower latency but higher CPU usage
     - Adjust crossfade to prevent audio clicks
     - Increase extra conversion size for better quality

5. **Start Realtime Conversion**:
   - Click "Start Realtime" button at the bottom
   - The status will change to "Running" (green)
   - Speak into your microphone
   - Your voice will be converted in realtime
   - Monitor latency in the "Status & Logs" tab

6. **Stop Conversion**:
   - Click "Stop Realtime" button
   - The audio processing will stop immediately

## Tips for Best Performance

1. **Low Latency Setup**:
   - Use SWIFT for F0 extraction
   - Set chunk size to 128-256 ms
   - Enable exclusive mode (WASAPI)
   - Use ASIO drivers if available
   - Close unnecessary applications

2. **High Quality Setup**:
   - Use RMVPE or FCPE for F0 extraction
   - Increase chunk size to 512+ ms
   - Increase extra conversion size to 1-2 seconds
   - Use index file with high search feature ratio (0.75-1.0)

3. **Virtual Audio Cable**:
   - Install a virtual audio cable (e.g., VB-Audio Cable)
   - Set output device to the virtual cable
   - Use the virtual cable as input in your target application (Discord, OBS, etc.)

4. **Troubleshooting**:
   - If you hear crackling: Increase chunk size or crossfade overlap
   - If latency is too high: Decrease chunk size and extra conversion size
   - If quality is poor: Increase search feature ratio and use index file
   - If voice cuts out: Disable VAD or adjust silence threshold
   - Check the "Status & Logs" tab for error messages

## Model Files

Place your model files in the `models/` directory or browse to them from anywhere on your system. The application supports:
- `.pth` files (PyTorch model weights)
- `.index` files (FAISS index for voice retrieval)

## Keyboard Shortcuts

- The application can be closed normally, and it will prompt you to stop realtime processing if it's running

## Advanced Configuration

All settings are adjustable through the GUI:

### Performance Settings
- **Chunk Size**: Audio buffer size (2.7-2730.7 ms)
- **Crossfade Overlap**: Fade duration between chunks (0.05-0.2 s)
- **Extra Conversion Size**: Context audio for model (0.1-5 s)
- **Silence Threshold**: Volume level for silence detection (-90 to -60 dB)

### Voice Settings
- **Pitch**: Semitone shift (-24 to +24)
- **Index Rate**: Feature retrieval influence (0-1)
- **Volume Envelope**: Output envelope blending (0-1)
- **Protect**: Consonant protection level (0-0.5)

## System Requirements

- **OS**: Windows, Linux, or macOS
- **Python**: 3.8 or higher
- **GPU**: CUDA-compatible GPU recommended for best performance
- **RAM**: 4GB minimum, 8GB+ recommended
- **Audio**: Working audio input/output devices

## Notes

- The application uses the same core RVC engine as the main Gradio interface
- All processing is done locally on your machine
- No internet connection required after initial setup
- Model files are not included - you need to train or obtain them separately

## Support

For issues or questions:
1. Check the "Status & Logs" tab for error messages
2. Ensure your model files are compatible with RVC
3. Verify audio devices are working properly
4. Check that all dependencies are installed

## License

This application is part of the Advanced-RVC-Inference project and follows the same license terms.