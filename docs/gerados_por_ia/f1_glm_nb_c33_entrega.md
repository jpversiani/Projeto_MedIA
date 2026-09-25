The user wants me to create a JavaScript file for WebRTC media management for a medical teleconsultation system (Projeto MedIA). The task is specifically:

Create `backend/app/static/js/webrtc_manager.js` with a `WebRTCManager` class:
- getUserMedia capture
- Dynamic microphone/camera selection
- Mute/unmute controls
- RTCPeerConnection manipulation for medical teleconsultation in modern browsers

The architecture guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage. However, the actual deliverable is a JavaScript file. The Python guidelines are mostly context for the project — the JS file itself can't be Python. But I should be mindful: the guidelines say "Manter conformidade total e cobertura de testes automatizados com pytest" — for a JS file, pytest doesn't apply directly, but I could mention how it would be tested (e.g., via Playwright/Selenium integration tests invoked from pytest, or Jest). I could optionally provide a small pytest wrapper that runs JS tests, but the core task is the JS file.

Let me focus on producing a high-quality, production-grade `webrtc_manager.js` with:

1. **WebRTCManager class** with:
   - Constructor with configuration options (STUN/TURN servers, constraints, callbacks)
   - `getUserMedia` capture with fallbacks (audio/video constraints)
   - Device enumeration (`enumerateDevices`) and dynamic selection (`switchMicrophone`, `switchCamera`) using `replaceTrack` or track constraints
   - Mute/unmute for audio and video (track.enabled toggling + local state)
   - `RTCPeerConnection` management: create offer/answer, ICE candidate handling, addTrack, renegotiation
   - Permission handling (Permission API, NotAllowedError, NotFoundError, NotReadableError, OverconstrainedError)
   - Device change events (`devicechange`)
   - Cleanup/dispose
   - Event emitter pattern for callbacks (onLocalStream, onRemoteStream, onIceCandidate, onConnectionStateChange, onDeviceListChange, onError)
   - Modern browser support: `navigator.mediaDevices`, secure context checks
   - LGPD considerations: consent for capture (medical context), no persistence of media, indicators

2. Medical context: teleconsulta — should include:
   - Consent verification before capture (LGPD Art. 20-ish / CFM Resolution 2.314/2022 for telemedicine in Brazil)
   - Session metadata hooks (e.g., patient CNS for audit trail — but careful, JS shouldn't log PHI; avoid logging sensitive data)
   - Quality adaptation (bandwidth, e.g., `sender.setParameters` with maxBitrate for video)
   - Stats monitoring (getStats for connection quality — packet loss, RTT) — useful for telehealth

3. Since the project uses Python backend with pytest, I can add a brief note and maybe a companion pytest test file that uses Playwright to test the JS in a browser, or a JS unit test. The instructions say "cobertura de testes automatizados com pytest" — I could include `backend/tests/test_webrtc_manager.py` using Playwright to load a fixture page and test the manager. That would align with the guidelines. But the primary task is the JS file. I'll deliver the JS file as the main artifact and include a pytest test harness (Playwright-based) as a bonus to satisfy the testing guideline, plus maybe a minimal HTML fixture.

Let me think about the JS design carefully.

```js
/**
 * MedIA — Módulo WebRTC de Gerenciamento de Mídia Local (C33)
 * ...
 */
```

Key API design:

```js
class WebRTCManager extends EventTarget (or custom emitter) {
  constructor(options = {})
  
  // Lifecycle
  async init()                    // checks secure context, enumerates devices
  async startLocalMedia(constraintsOverride)  // getUserMedia
  async stopLocalMedia()
  
  // Device selection
  async listMicrophones()
  async listCameras()
  async listSpeakers()            // output devices (may need permission)
  async switchMicrophone(deviceId)
  async switchCamera(deviceId)
  
  // Controls
  toggleAudioMute(force)
  toggleVideoMute(force)
  isAudioMuted()
  isVideoMuted()
  
  // Peer connection
  async createPeerConnection()
  async createOffer()
  async createAnswer(offerSdp)
  async setRemoteDescription(sdp, type)
  async addIceCandidate(candidate)
  async replaceTrackKind / internal
  setRemoteStream(stream) // ontrack handles it
  
  // Quality/stats
  async getConnectionStats()
  async setVideoBitrate(kbps)
  enableAdaptiveQuality?
  
  // Cleanup
  destroy()
}
```

Events via EventTarget (modern, standard): dispatch CustomEvents: `localstream`, `remotestream`, `icecandidate`, `connectionstatechange`, `deviceschanged`, `error`, `track`, `stats`, `permissionstate`.

Implementation details:

- **Secure context check**: `window.isSecureContext` — getUserMedia requires HTTPS or localhost. Throw/emit error otherwise.
- **Feature detection**: `navigator.mediaDevices?.getUserMedia` — fallback error message.
- **Constraints**: default `{ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }, video: { width: {ideal: 1280}, height: {ideal: 720}, frameRate: {ideal: 30, max: 30}, facingMode: 'user' } }`. For medical teleconsultation, good audio quality matters (ausculta? no — but speech clarity). Maybe allow `audioOnly` mode for low bandwidth.
- **Device selection**: after getUserMedia with a device, `enumerateDevices` returns labels. Switching: get new stream with `deviceId: {exact: id}` for the kind, then `sender.replaceTrack(newTrack)` on the existing peer connection to avoid renegotiation. Stop old track. Keep the same stream? Better approach: maintain `this._localStream`, replace track within it via `stream.removeTrack(old); stream.addTrack(new)` — but that triggers renegotiation if using addTrack... Actually with `replaceTrack` on senders, no renegotiation needed. The local stream object mutation is fine for local preview (video element srcObject stays same stream object; replacing tracks within it works — the video element continues rendering the new track if we remove+add? Actually MediaStream track changes: if you remove a track and add another, consumers like `<video>` will pick it up in modern browsers? It's safer to dispatch event and let UI re-attach, or keep the same stream and just swap tracks — Chrome/Firefox handle track replacement within a stream attached to a video element reasonably, but the spec-wise safe approach is to dispatch an event `localstreamchanged` or `trackreplaced` so the UI can update. I'll dispatch events.

- **Mute/unmute**: `track.enabled = false/true`. Track `this._audioMuted`, `this._videoMuted` state. Dispatch `audiomuted`/`videomuted` events. Note: muting via enabled=false keeps the track live and doesn't require renegotiation — correct approach.

- **RTCPeerConnection**:
  - Config: `iceServers` (STUN: stun.l.google.com:19302 default; TURN configurable — for healthcare, TURN over TLS, credentials from backend ephemeral tokens — I'll support `iceServers` option and note ephemeral credential fetching hook `getIceServers` async callback).
  - `createPeerConnection()`: new RTCPeerConnection with config; add local tracks; `ontrack` → build remote stream, dispatch `remotestream`; `onicecandidate` → dispatch `icecandidate`; `onconnectionstatechange` / `oniceconnectionstatechange` → dispatch; `onicegatheringstatechange`.
  - Perfect negotiation pattern? For a medical teleconsultation, one side is typically the professional (polite/impolite). I can implement basic perfect negotiation support with `polite` flag — that's modern best practice. Might be overkill but shows quality. I'll include a simplified renegotiation handler: `onnegotiationneeded` → create offer (only if we're the impolite peer or via signaling coordination). Hmm, to keep it robust but not overly complex, I'll implement the perfect negotiation pattern from the spec (polite/impolite with rollback handling). That's genuinely "manipulação de RTCPeerConnection" at a high level. Let me include it — it's the modern standard and handles glare.

  Perfect negotiation:
  ```js
  async _onNegotiationNeeded() {
    try {
      this._makingOffer = true;
      await this._pc.setLocalDescription(); // implicit offer
      this._emit('negotiationneeded', { sdp: this._pc.localDescription });
    } finally { this._makingOffer = false; }
  }
  
  async handleRemoteDescription(desc) {
    const offerCollision = desc.type === 'offer' && (this._makingOffer || (this._pc.signalingState !== 'stable' && !this._isSettingRemoteAnswerPending));
    this._ignoreOffer = !this._polite && offerCollision;
    if (this._ignoreOffer) return;
    this._isSettingRemoteAnswerPending = desc.type === 'answer';
    await this._pc.setRemoteDescription(desc);
    this._isSettingRemoteAnswerPending = false;
    if (desc.type === 'offer') {
      await this._pc.setLocalDescription();
      this._emit('negotiationneeded', { sdp: this._pc.localDescription });
    }
  }
  ```
  
  And `addIceCandidate` with ignore-offer-on-error for polite peer.

- **Stats**: `pc.getStats()` → parse for packetsLost, jitter, RTT, bytesSent/Received, frame rate. Emit `stats` periodically if `statsInterval` configured. Useful for telehealth quality monitoring (CFM requires quality safeguards).

- **Bandwidth control**: `sender.getParameters()` → `parameters.encodings[0].maxBitrate = kbps*1000` → `setParameters`. 

- **Error taxonomy**: map DOMException names to friendly Portuguese messages: NotAllowedError (permissão negada), NotFoundError (dispositivo não encontrado), NotReadableError (dispositivo em uso), OverconstrainedError, SecurityError, AbortError. Emit `error` events with structured `{ code, message, original }`.

- **LGPD/consent**: option `requireConsent: true` — before getUserMedia, check a consent callback or just document. I'll add a `consent` hook: `options.onConsentRequest` async that must return true; if not provided and `requireConsent` true, log warning? For a medical app, capturing audio/video requires patient consent (CFM 2.314/2022, LGPD). I'll implement: if `requireConsent` (default true) and no consent handler, throw config error. Actually to keep it usable, default `requireConsent: false` but strongly documented? Hmm. Better: default true with a built-in check that the integrator supplies `options.consentHandler`. But that could break simple usage. I'll make it: `requireConsent` default `true`, and `consentHandler` optional async function; if requireConsent is true and no handler, we emit a warning and proceed? No — for compliance, better to fail closed? That's harsh for dev. Let me make default `requireConsent: false` but document that production telehealth must set it true with a handler. Actually, since this is a compliance-focused project (SUS/APS), I'll default `requireConsent: true` and provide `consentHandler` — if missing, throw a `ConfigurationError` with clear message. That demonstrates compliance-first design. Hmm, but then the module won't work out of the box... The task says "conformidade total". I'll go with fail-closed default true, and document clearly. Actually let me reconsider: the manager is a low-level media module; consent is typically handled by the UI layer before instantiating. I'll implement it as: `requireConsent` (default true) + `consentHandler` (async () => boolean). If requireConsent && !consentHandler → throw ConfigurationError at init/start. That's clean and compliant.

- **No PHI in logs**: logger redacts; never log device labels? Device labels aren't PHI but could be identifying; I'll keep logs minimal, no stream data. Provide `debug` flag.

- **CNS/CPF**: not really relevant to JS module; maybe session metadata option `sessionContext: { consultationId, patientCnsMasked }` used only for audit events? I should avoid handling CNS in JS. I can include an optional `session` metadata object attached to emitted events (e.g., stats events include `consultationId`) for correlation with backend audit logs. Keep it minimal and note that identifiers must be masked/pseudonymized client-side. I'll add `options.sessionId` (opaque) included in emitted events — no CNS handling in the browser.

- **Device change listener**: `navigator.mediaDevices.addEventListener('devicechange', ...)` → re-enumerate, dispatch `deviceschanged`. Debounce.

- **Permission API**: `navigator.permissions.query({name:'camera'})` and `'microphone'` to pre-check state; handle browsers that don't support it (Safari). Emit `permissionstate`.

- **Audio output selection**: `HTMLMediaElement.setSinkId` for speaker selection (Chrome/Edge). Include `setSpeaker(deviceId, videoElement)`.

- **Screen sharing?** Not requested. Skip, or mention as extension. Task says capture, device selection, mute, RTCPeerConnection. Keep scope tight but complete. Maybe include `toggleScreenShare`? Not requested — I'll leave it out to keep the module focused, or add briefly? I'll skip to avoid bloat; maybe mention in comments as future. Actually screen share is common in teleconsultation (share exam images). Hmm, task is specific; I'll not add it. Keep focused.

- **Audio-only fallback**: if video fails but audio succeeds (e.g., camera busy), retry with audio-only? Provide `fallbackToAudioOnly` option. Good for telemedicine on poor devices. Implement: on NotReadableError/NotFoundError for video, retry with `{audio: true, video: false}` if option enabled.

- **Track ended handling**: `track.onended` (e.g., device unplugged) → dispatch event, attempt recovery.

- **Reconnection**: ICE restart support: `async restartIce()` → `pc.restartIce()` or create offer with iceRestart. Include.

Structure of the file:

```js
/* SPDX-License-Identifier: AGPL-3.0-or-later (or project license) */
/**
 * MedIA · C33 — Módulo WebRTC de Gerenciamento de Mídia Local
 * ...
 * Conformidade: LGPD (Lei 13.709/2018), CFM Res. 2.314/2022, ...
 */

'use strict';

// Constants: MediaKind enum-ish, error codes, defaults.

class WebRTCError extends Error { constructor(code, message, cause) ... }

class WebRTCManager extends EventTarget {
  #private fields (use real private fields — modern browsers)
  constructor(options)
  // ... methods
}

// Export: ES module + UMD-ish global for non-module pages
export default WebRTCManager; // and named
if (typeof window !== 'undefined') window.WebRTCManager = WebRTCManager;
```

Since it's served from Flask static and might be included via `<script>` (not module), I should support both: use a pattern that works as plain script and as module. Options:
- Write as plain script defining class on window, with UMD check.
- Or write ES module and instruct `<script type="module">`.

Best: write it as an ES module but with a guard that also attaches to window when loaded as classic script? A file with `export` statements fails as classic script. To support both, avoid `export` and attach to `window`, plus `export` at the end guarded? Can't conditionally export. Common approach: provide the file as a classic script attaching to `window.WebRTCManager`, and note that ES module usage can `import` it via a wrapper. Alternatively write ES module and require `<script type="module">`. Modern browsers support modules fine. Flask template: `<script type="module" src="...">`. I'll write it as an ES module with `export { WebRTCManager }` and `export default`, and also attach to `window` for convenience when bundled. Hmm — attaching to window in a module is fine. But if someone loads it as classic script it breaks on `export`. I'll document: load with `type="module"`. That's "navegadores modernos" compliant. Good.

Actually, to maximize compatibility (some legacy pages), I could do the dual pattern:

```js
(function (global) {
  class WebRTCManager extends EventTarget { ... }
  global.MedIA = global.MedIA || {};
  global.MedIA.WebRTCManager = WebRTCManager;
  if (typeof module !== 'undefined' && module.exports) module.exports = WebRTCManager;
})(typeof window !== 'undefined' ? window : globalThis);
```

But ES modules are cleaner and the task says modern browsers. I'll go ES module with window attach fallback comment. Let me do: ES module, `export default WebRTCManager; export { WebRTCManager };` and also `if (typeof window !== 'undefined') window.WebRTCManager = WebRTCManager;` so a `<script type="module">` include makes it globally available too. 

Private fields: use `#field` syntax — supported in all modern browsers (Chrome 74+, FF 90+, Safari 14.1+). Fine.

Now, detailed implementation:

```js
const MediaKind = Object.freeze({ AUDIO: 'audio', VIDEO: 'video' });

const ErrorCodes = Object.freeze({
  NOT_INITIALIZED: 'WEBRTC_NOT_INITIALIZED',
  INSECURE_CONTEXT: 'WEBRTC_INSECURE_CONTEXT',
  UNSUPPORTED: 'WEBRTC_UNSUPPORTED',
  CONFIG_INVALID: 'WEBRTC_CONFIG_INVALID',
  CONSENT_DENIED: 'WEBRTC_CONSENT_DENIED',
  PERMISSION_DENIED: 'NotAllowedError',
  DEVICE_NOT_FOUND: 'NotFoundError',
  DEVICE_IN_USE: 'NotReadableError',
  OVERCONSTRAINED: 'OverconstrainedError',
  DEVICE_UNPLUGGED: 'WEBRTC_DEVICE_UNPLUGGED',
  SWITCH_FAILED: 'WEBRTC_SWITCH_FAILED',
  PEER_CONNECTION: 'WEBRTC_PEER_CONNECTION',
  SIGNALING: 'WEBRTC_SIGNALING',
  DESTROYED: 'WEBRTC_DESTROYED',
});
```

Defaults:

```js
const DEFAULTS = Object.freeze({
  iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }],
  iceCandidatePoolSize: 2,
  bundlePolicy: 'max-bundle',
  rtcpMuxPolicy: 'require',
  video: { width: