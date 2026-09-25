/**
 * VoiceClient — wraps MediaRecorder + the /ws/voice WebSocket.
 *
 * Usage:
 *   const voice = new VoiceClient({
 *     onStatus: (msg) => {...},
 *     onResult: (text) => {...},
 *     onError:  (msg) => {...},
 *   });
 *   await voice.start();  // begins recording
 *   voice.stop();         // stops recording, triggers transcription
 */

class VoiceClient {
  constructor({ onStatus, onResult, onError } = {}) {
    this.onStatus = onStatus || (() => {});
    this.onResult = onResult || (() => {});
    this.onError = onError || (() => {});

    this.ws = null;
    this.mediaRecorder = null;
    this.mediaStream = null;
    this.isRecording = false;
  }

  _wsUrl() {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}/ws/voice`;
  }

  async _ensureSocket() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

    await new Promise((resolve, reject) => {
      this.ws = new WebSocket(this._wsUrl());

      this.ws.onopen = () => resolve();
      this.ws.onerror = () => {
        this.onError("Unable to connect to the voice server. Please check your connection.");
        reject(new Error("WebSocket connection failed"));
      };
      this.ws.onclose = () => {
        if (this.isRecording) {
          this.onError("Voice connection was lost. Please try again.");
          this.isRecording = false;
        }
      };
      this.ws.onmessage = (event) => this._handleMessage(event);
    });
  }

  _handleMessage(event) {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch {
      return;
    }

    if (payload.type === "status") {
      this.onStatus(payload.message);
    } else if (payload.type === "result") {
      this.onResult(payload.text);
    } else if (payload.type === "error") {
      this.onError(payload.message);
    }
  }

  async start() {
    if (this.isRecording) return;

    // 1. Microphone permission
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      this.onError("Microphone permission is required to use voice input.");
      throw err;
    }

    // 2. WebSocket connection
    try {
      await this._ensureSocket();
    } catch (err) {
      this._releaseStream();
      throw err;
    }

    // 3. Start recorder + tell server we're starting
    const mimeType = this._pickMimeType();
    this.mediaRecorder = new MediaRecorder(this.mediaStream, mimeType ? { mimeType } : undefined);

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
        e.data.arrayBuffer().then((buf) => this.ws.send(buf));
      }
    };

    this.ws.send(JSON.stringify({ type: "start" }));
    this.mediaRecorder.start(250); // emit chunks every 250ms
    this.isRecording = true;
  }

  stop() {
    if (!this.isRecording) return;
    this.isRecording = false;

    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    this._releaseStream();

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Small delay so the final ondataavailable chunk is sent first.
      setTimeout(() => this.ws.send(JSON.stringify({ type: "stop" })), 150);
    }
  }

  cancel() {
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    this._releaseStream();
    this.isRecording = false;
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "cancel" }));
    }
  }

  _releaseStream() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
  }

  _pickMimeType() {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
    ];
    for (const type of candidates) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) return type;
    }
    return null;
  }
}

window.VoiceClient = VoiceClient;
