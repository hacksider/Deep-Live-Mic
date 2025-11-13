"""
Realtime Voice Cloning with Tkinter GUI
Allows loading PTH model files and performing realtime voice conversion
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import sys
from pathlib import Path
import numpy as np

# Add programs directory to path
now_dir = os.getcwd()
sys.path.append(now_dir)

from programs.applio_code.rvc.realtime.callbacks import AudioCallbacks
from programs.applio_code.rvc.realtime.audio import list_audio_device
from programs.applio_code.rvc.realtime.core import AUDIO_SAMPLE_RATE


class RealtimeVoiceCloningGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Realtime Voice Cloning - RVC")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        
        # State variables
        self.model_path = tk.StringVar()
        self.index_path = tk.StringVar()
        self.is_running = False
        self.callbacks = None
        self.audio_manager = None
        self.log_queue = queue.Queue()
        self.status_update_job = None
        
        # Audio device lists
        self.input_devices = {}
        self.output_devices = {}
        
        # Configuration variables
        self.pitch = tk.IntVar(value=0)
        self.index_rate = tk.DoubleVar(value=0.75)
        self.volume_envelope = tk.DoubleVar(value=1.0)
        self.protect = tk.DoubleVar(value=0.5)
        self.f0_method = tk.StringVar(value="swift")
        self.embedder_model = tk.StringVar(value="contentvec")
        self.chunk_size = tk.DoubleVar(value=512)
        self.crossfade_overlap = tk.DoubleVar(value=0.01)
        self.extra_convert_size = tk.DoubleVar(value=0.5)
        self.silent_threshold = tk.IntVar(value=-90)
        self.input_gain = tk.IntVar(value=100)
        self.output_gain = tk.IntVar(value=100)
        self.vad_enabled = tk.BooleanVar(value=True)
        self.exclusive_mode = tk.BooleanVar(value=True)
        self.autotune = tk.BooleanVar(value=False)
        self.autotune_strength = tk.DoubleVar(value=1.0)
        
        self.setup_ui()
        self.refresh_audio_devices()
        self.update_log_display()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main container with notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_model_tab()
        self.setup_audio_tab()
        self.setup_settings_tab()
        self.setup_log_tab()
        
        # Control buttons at bottom
        self.setup_control_buttons()
        
    def setup_model_tab(self):
        """Setup model selection tab"""
        model_frame = ttk.Frame(self.notebook)
        self.notebook.add(model_frame, text="Model")
        
        # Model file selection
        ttk.Label(model_frame, text="Model File (.pth):", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        
        model_entry_frame = ttk.Frame(model_frame)
        model_entry_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        model_entry_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(model_entry_frame, textvariable=self.model_path, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(model_entry_frame, text="Browse", command=self.browse_model).grid(
            row=0, column=1
        )
        
        # Index file selection
        ttk.Label(model_frame, text="Index File (.index) - Optional:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=(15, 5)
        )
        
        index_entry_frame = ttk.Frame(model_frame)
        index_entry_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        index_entry_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(index_entry_frame, textvariable=self.index_path, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(index_entry_frame, text="Browse", command=self.browse_index).grid(
            row=0, column=1
        )
        ttk.Button(index_entry_frame, text="Clear", command=lambda: self.index_path.set("")).grid(
            row=0, column=2, padx=(5, 0)
        )
        
        # Model info display
        info_frame = ttk.LabelFrame(model_frame, text="Model Information", padding=10)
        info_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=15)
        model_frame.rowconfigure(4, weight=1)
        
        self.model_info_text = scrolledtext.ScrolledText(
            info_frame, height=15, wrap=tk.WORD, state='disabled'
        )
        self.model_info_text.pack(fill=tk.BOTH, expand=True)
        
        model_frame.columnconfigure(0, weight=1)
        
    def setup_audio_tab(self):
        """Setup audio device selection tab"""
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="Audio Devices")
        
        # Refresh button
        ttk.Button(audio_frame, text="Refresh Devices", command=self.refresh_audio_devices).grid(
            row=0, column=0, columnspan=2, pady=10, padx=10, sticky=tk.W
        )
        
        # Input device
        ttk.Label(audio_frame, text="Input Device:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        self.input_device_combo = ttk.Combobox(audio_frame, state='readonly', width=50)
        self.input_device_combo.grid(row=2, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(audio_frame, text="Input Gain (%):", font=("Arial", 9)).grid(
            row=3, column=0, sticky=tk.W, padx=10, pady=(5, 0)
        )
        ttk.Scale(audio_frame, from_=0, to=200, variable=self.input_gain, orient=tk.HORIZONTAL).grid(
            row=4, column=0, padx=10, pady=5, sticky=(tk.W, tk.E)
        )
        ttk.Label(audio_frame, textvariable=self.input_gain).grid(
            row=4, column=1, padx=5
        )
        
        # Output device
        ttk.Label(audio_frame, text="Output Device:", font=("Arial", 10, "bold")).grid(
            row=5, column=0, sticky=tk.W, padx=10, pady=(15, 5)
        )
        self.output_device_combo = ttk.Combobox(audio_frame, state='readonly', width=50)
        self.output_device_combo.grid(row=6, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(audio_frame, text="Output Gain (%):", font=("Arial", 9)).grid(
            row=7, column=0, sticky=tk.W, padx=10, pady=(5, 0)
        )
        ttk.Scale(audio_frame, from_=0, to=200, variable=self.output_gain, orient=tk.HORIZONTAL).grid(
            row=8, column=0, padx=10, pady=5, sticky=(tk.W, tk.E)
        )
        ttk.Label(audio_frame, textvariable=self.output_gain).grid(
            row=8, column=1, padx=5
        )
        
        # Audio options
        options_frame = ttk.LabelFrame(audio_frame, text="Audio Options", padding=10)
        options_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=15)
        
        ttk.Checkbutton(options_frame, text="Enable VAD (Voice Activity Detection)", 
                       variable=self.vad_enabled).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Exclusive Mode (WASAPI - Lower Latency)", 
                       variable=self.exclusive_mode).pack(anchor=tk.W, pady=2)
        
        audio_frame.columnconfigure(0, weight=1)
        
    def setup_settings_tab(self):
        """Setup voice conversion settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Voice Settings")
        
        # Create scrollable frame
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pitch
        ttk.Label(scrollable_frame, text="Pitch Shift (semitones):", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        pitch_frame = ttk.Frame(scrollable_frame)
        pitch_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        ttk.Scale(pitch_frame, from_=-24, to=24, variable=self.pitch, orient=tk.HORIZONTAL).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Label(pitch_frame, textvariable=self.pitch, width=5).pack(side=tk.LEFT, padx=5)
        
        # Index Rate
        ttk.Label(scrollable_frame, text="Search Feature Ratio:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        index_frame = ttk.Frame(scrollable_frame)
        index_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        ttk.Scale(index_frame, from_=0, to=1, variable=self.index_rate, orient=tk.HORIZONTAL).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Label(index_frame, textvariable=self.index_rate, width=5).pack(side=tk.LEFT, padx=5)
        
        # Volume Envelope
        ttk.Label(scrollable_frame, text="Volume Envelope:", font=("Arial", 10, "bold")).grid(
            row=4, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        volume_frame = ttk.Frame(scrollable_frame)
        volume_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        ttk.Scale(volume_frame, from_=0, to=1, variable=self.volume_envelope, orient=tk.HORIZONTAL).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Label(volume_frame, textvariable=self.volume_envelope, width=5).pack(side=tk.LEFT, padx=5)
        
        # Protect
        ttk.Label(scrollable_frame, text="Protect Voiceless Consonants:", font=("Arial", 10, "bold")).grid(
            row=6, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        protect_frame = ttk.Frame(scrollable_frame)
        protect_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        ttk.Scale(protect_frame, from_=0, to=0.5, variable=self.protect, orient=tk.HORIZONTAL).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Label(protect_frame, textvariable=self.protect, width=5).pack(side=tk.LEFT, padx=5)
        
        # F0 Method
        ttk.Label(scrollable_frame, text="Pitch Extraction Method:", font=("Arial", 10, "bold")).grid(
            row=8, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        f0_frame = ttk.Frame(scrollable_frame)
        f0_frame.grid(row=9, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Radiobutton(f0_frame, text="RMVPE", variable=self.f0_method, value="rmvpe").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(f0_frame, text="FCPE", variable=self.f0_method, value="fcpe").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(f0_frame, text="SWIFT", variable=self.f0_method, value="swift").pack(side=tk.LEFT, padx=5)
        
        # Embedder Model
        ttk.Label(scrollable_frame, text="Embedder Model:", font=("Arial", 10, "bold")).grid(
            row=10, column=0, sticky=tk.W, padx=10, pady=(10, 5)
        )
        embedder_combo = ttk.Combobox(scrollable_frame, textvariable=self.embedder_model, 
                                     values=["contentvec", "spin", "chinese-hubert-base", 
                                            "japanese-hubert-base", "korean-hubert-base"],
                                     state='readonly', width=30)
        embedder_combo.grid(row=11, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Autotune
        autotune_frame = ttk.LabelFrame(scrollable_frame, text="Autotune", padding=10)
        autotune_frame.grid(row=12, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Checkbutton(autotune_frame, text="Enable Autotune", 
                       variable=self.autotune).pack(anchor=tk.W, pady=2)
        
        ttk.Label(autotune_frame, text="Autotune Strength:").pack(anchor=tk.W, pady=(5, 0))
        strength_frame = ttk.Frame(autotune_frame)
        strength_frame.pack(fill=tk.X, pady=5)
        ttk.Scale(strength_frame, from_=0, to=1, variable=self.autotune_strength, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(strength_frame, textvariable=self.autotune_strength, width=5).pack(side=tk.LEFT, padx=5)
        
        # Performance Settings
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance Settings", padding=10)
        perf_frame.grid(row=13, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(perf_frame, text="Chunk Size (ms):").pack(anchor=tk.W)
        chunk_frame = ttk.Frame(perf_frame)
        chunk_frame.pack(fill=tk.X, pady=5)
        ttk.Scale(chunk_frame, from_=2.7, to=2730.7, variable=self.chunk_size, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(chunk_frame, textvariable=self.chunk_size, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(perf_frame, text="Crossfade Overlap (s):").pack(anchor=tk.W, pady=(5, 0))
        cross_frame = ttk.Frame(perf_frame)
        cross_frame.pack(fill=tk.X, pady=5)
        ttk.Scale(cross_frame, from_=0.05, to=0.2, variable=self.crossfade_overlap, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(cross_frame, textvariable=self.crossfade_overlap, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(perf_frame, text="Extra Conversion Size (s):").pack(anchor=tk.W, pady=(5, 0))
        extra_frame = ttk.Frame(perf_frame)
        extra_frame.pack(fill=tk.X, pady=5)
        ttk.Scale(extra_frame, from_=0.1, to=5, variable=self.extra_convert_size, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(extra_frame, textvariable=self.extra_convert_size, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(perf_frame, text="Silence Threshold (dB):").pack(anchor=tk.W, pady=(5, 0))
        silent_frame = ttk.Frame(perf_frame)
        silent_frame.pack(fill=tk.X, pady=5)
        ttk.Scale(silent_frame, from_=-90, to=-60, variable=self.silent_threshold, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(silent_frame, textvariable=self.silent_threshold, width=8).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scrollable_frame.columnconfigure(0, weight=1)
        
    def setup_log_tab(self):
        """Setup log/status tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Status & Logs")
        
        # Status label
        self.status_label = ttk.Label(log_frame, text="Status: Not Running", 
                                     font=("Arial", 12, "bold"), foreground="red")
        self.status_label.pack(pady=10)
        
        # Latency display
        self.latency_label = ttk.Label(log_frame, text="Latency: -- ms", 
                                      font=("Arial", 10))
        self.latency_label.pack(pady=5)
        
        # Log text area
        ttk.Label(log_frame, text="Logs:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Logs", command=self.clear_logs).pack(pady=5)
        
    def setup_control_buttons(self):
        """Setup start/stop control buttons"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Realtime", 
                                       command=self.start_realtime, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5, ipadx=20, ipady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Realtime", 
                                     command=self.stop_realtime, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5, ipadx=20, ipady=5)
        
    def browse_model(self):
        """Browse for model file"""
        filename = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[("PyTorch Model", "*.pth"), ("All Files", "*.*")]
        )
        if filename:
            self.model_path.set(filename)
            self.log_message(f"Model selected: {filename}")
            self.display_model_info(filename)
            
    def browse_index(self):
        """Browse for index file"""
        filename = filedialog.askopenfilename(
            title="Select Index File",
            filetypes=[("Index File", "*.index"), ("All Files", "*.*")]
        )
        if filename:
            self.index_path.set(filename)
            self.log_message(f"Index selected: {filename}")
            
    def display_model_info(self, model_path):
        """Display model information"""
        self.model_info_text.config(state='normal')
        self.model_info_text.delete(1.0, tk.END)
        
        try:
            import torch
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
            
            info = f"Model Path: {model_path}\n\n"
            info += f"Model Version: {checkpoint.get('version', 'v1')}\n"
            info += f"Sample Rate: {checkpoint['config'][-1]} Hz\n"
            info += f"Uses F0: {'Yes' if checkpoint.get('f0', 1) else 'No'}\n"
            info += f"Vocoder: {checkpoint.get('vocoder', 'HiFi-GAN')}\n"
            info += f"Speakers: {checkpoint['weight']['emb_g.weight'].shape[0]}\n"
            
            self.model_info_text.insert(1.0, info)
        except Exception as e:
            self.model_info_text.insert(1.0, f"Error loading model info:\n{str(e)}")
        
        self.model_info_text.config(state='disabled')
        
    def refresh_audio_devices(self):
        """Refresh audio device lists"""
        try:
            input_devices, output_devices = list_audio_device()
            
            # Sort devices
            def priority(device):
                n = device.name.lower()
                if "virtual" in n:
                    return 0
                if "vb" in n:
                    return 1
                return 2
            
            input_sorted = sorted(input_devices, key=priority, reverse=True)
            output_sorted = sorted(output_devices, key=priority)
            
            # Create device dictionaries
            self.input_devices = {
                f"{i+1}: {d.name} ({d.host_api})": d.index
                for i, d in enumerate(input_sorted)
            }
            self.output_devices = {
                f"{i+1}: {d.name} ({d.host_api})": d.index
                for i, d in enumerate(output_sorted)
            }
            
            # Update comboboxes
            self.input_device_combo['values'] = list(self.input_devices.keys())
            self.output_device_combo['values'] = list(self.output_devices.keys())
            
            if self.input_devices:
                self.input_device_combo.current(0)
            if self.output_devices:
                self.output_device_combo.current(0)
                
            self.log_message(f"Found {len(self.input_devices)} input and {len(self.output_devices)} output devices")
            
        except Exception as e:
            self.log_message(f"Error refreshing audio devices: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh audio devices:\n{str(e)}")
            
    def start_realtime(self):
        """Start realtime voice conversion"""
        # Validate inputs
        if not self.model_path.get():
            messagebox.showerror("Error", "Please select a model file!")
            return
            
        if not self.input_device_combo.get() or not self.output_device_combo.get():
            messagebox.showerror("Error", "Please select input and output devices!")
            return
            
        try:
            # Get device IDs
            input_device_id = self.input_devices[self.input_device_combo.get()]
            output_device_id = self.output_devices[self.output_device_combo.get()]
            
            # Calculate read chunk size
            read_chunk_size = int(self.chunk_size.get() * AUDIO_SAMPLE_RATE / 1000 / 128)
            
            # Create callbacks
            self.callbacks = AudioCallbacks(
                pass_through=False,
                read_chunk_size=read_chunk_size,
                cross_fade_overlap_size=self.crossfade_overlap.get(),
                extra_convert_size=self.extra_convert_size.get(),
                model_path=self.model_path.get(),
                index_path=self.index_path.get(),
                f0_method=self.f0_method.get(),
                embedder_model=self.embedder_model.get(),
                embedder_model_custom=None,
                silent_threshold=self.silent_threshold.get(),
                f0_up_key=self.pitch.get(),
                index_rate=self.index_rate.get(),
                protect=self.protect.get(),
                volume_envelope=self.volume_envelope.get(),
                f0_autotune=self.autotune.get(),
                f0_autotune_strength=self.autotune_strength.get(),
                proposed_pitch=False,
                proposed_pitch_threshold=155.0,
                input_audio_gain=self.input_gain.get() / 100.0,
                output_audio_gain=self.output_gain.get() / 100.0,
                monitor_audio_gain=1.0,
                monitor=False,
                vad_enabled=self.vad_enabled.get(),
                vad_sensitivity=3,
                vad_frame_ms=30,
                sid=0,
            )
            
            self.audio_manager = self.callbacks.audio
            self.audio_manager.start(
                input_device_id=input_device_id,
                output_device_id=output_device_id,
                output_monitor_id=None,
                exclusive_mode=self.exclusive_mode.get(),
                asio_input_channel=-1,
                asio_output_channel=-1,
                asio_output_monitor_channel=-1,
                read_chunk_size=read_chunk_size,
            )
            
            self.is_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text="Status: Running", foreground="green")
            
            self.log_message("Realtime voice conversion started!")
            
            # Start status update loop
            self.update_status()
            
        except Exception as e:
            self.log_message(f"Error starting realtime: {str(e)}")
            messagebox.showerror("Error", f"Failed to start realtime:\n{str(e)}")
            self.stop_realtime()
            
    def stop_realtime(self):
        """Stop realtime voice conversion"""
        try:
            self.is_running = False
            
            if self.audio_manager is not None:
                self.audio_manager.stop()
                self.audio_manager = None
                
            if self.callbacks is not None:
                self.callbacks = None
                
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="Status: Not Running", foreground="red")
            self.latency_label.config(text="Latency: -- ms")
            
            # Cancel status update
            if self.status_update_job:
                self.root.after_cancel(self.status_update_job)
                self.status_update_job = None
            
            self.log_message("Realtime voice conversion stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping realtime: {str(e)}")
            
    def update_status(self):
        """Update status display"""
        if self.is_running and self.audio_manager is not None:
            if hasattr(self.audio_manager, 'latency'):
                self.latency_label.config(text=f"Latency: {self.audio_manager.latency:.2f} ms")
            
            # Schedule next update
            self.status_update_job = self.root.after(100, self.update_status)
            
    def log_message(self, message):
        """Add message to log queue"""
        self.log_queue.put(message)
        
    def update_log_display(self):
        """Update log display from queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(100, self.update_log_display)
        
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
        
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Realtime is running. Stop and quit?"):
                self.stop_realtime()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = RealtimeVoiceCloningGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()