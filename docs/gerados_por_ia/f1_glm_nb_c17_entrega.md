The user is asking me to create a WebRTC media management module for a medical teleconsultation project (MedIA). The task is specifically about creating a JavaScript file: `backend/app/static/js/webrtc_manager.js` with a `WebRTCManager` class.

The task mentions:
- getUserMedia capture
- Dynamic microphone/camera selection
- Mute/unmute controls
- RTCPeerConnection handling for medical teleconsultation in modern browsers

The architecture guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (Brazilian health system), CIAP-2, CID-10, SOAP method, CNS/CPF identification, pytest coverage.

However, the actual deliverable is a JavaScript file. The Python guidelines are somewhat contradictory here since the main file is JS. I should focus on the JavaScript file as the primary deliverable, but I can note that the surrounding architecture is Python-based. Since the task explicitly says to create `backend/app/static/js/webrtc_manager.js`, that's the main artifact.

Let me think about what a robust WebRTCManager class for medical teleconsultation should include:

1. **Device enumeration**: `navigator.mediaDevices.enumerateDevices()` to list cameras and microphones
2. **getUserMedia capture**: with constraints for audio/video, handling permission errors
3. **Dynamic device switching**: switching microphone/camera mid-call without renegotiation (using `replaceTrack`)
4. **Mute/unmute**: audio and video toggles (enabled property on tracks)
5. **RTCPeerConnection**: offer/answer, ICE candidates handling, signaling via WebSocket (I'll abstract the signaling layer with callbacks so it can be plugged into any backend signaling)
6. **Medical context considerations**:
   - LGPD compliance (Brazilian data protection law) - consent handling
   - Audit logging hooks (for medical records)
   - Connection quality monitoring (important for telehealth)
   - Graceful degradation (audio-only fallback if video fails)
   - Secure context requirement (HTTPS) - mandatory for getUserMedia
   - Cleanup/disposal of resources (privacy - stop all tracks)
   - Screen sharing capability (useful for showing exam results, documents)
   - Data channels possibly for chat/metadata
   - Recording considerations (with consent flags - important in medical context)

7. **Error handling**: NotAllowedError, NotFoundError, NotReadableError, OverconstrainedError, SecurityError

8. **Browser compatibility**: modern browsers, handle vendor prefixes minimally (modern browsers don't need prefixes anymore), but handle `navigator.mediaDevices` absence (insecure context)

Let me structure the class:

```javascript
class WebRTCManager {
    constructor(options) { ... }
    
    // Lifecycle
    async initialize()
    async startLocalMedia(constraints)
    async stopLocalMedia()
    destroy()
    
    // Devices
    async enumerateDevices()
    async switchMicrophone(deviceId)
    async switchCamera(deviceId)
    async switchSpeaker(deviceId) // setSinkId
    
    // Controls
    toggleAudio(enabled)
    toggleVideo(enabled)
    async startScreenShare()
    async stopScreenShare()
    
    // Connection
    async connect(sessionId)
    async createOffer()
    async handleOffer(offer)
    async handleAnswer(answer)
    async handleIceCandidate(candidate)
    async renegotiate()
    
    // Quality/stats
    async getConnectionStats()
    startQualityMonitoring()
    
    // Events
    on(event, callback)
    emit(event, data)
}
```

For the medical context, I should include:
- Session metadata (patient/professional IDs, CNS maybe — but careful with sensitive data in JS; I'll keep it minimal and note LGPD)
- Audit event hooks
- Consent verification before media capture
- Secure context check

Since the guidelines mention pytest coverage, I should also provide a test file. But testing JS with pytest? That's odd. The guidelines say "cobertura de testes automatizados com pytest" — for the JS module, tests would typically be Jest/Vitest. However, the user's guidelines say pytest. I could provide a pytest test that validates the JS file exists and maybe runs basic syntax checks, or I could provide Jest tests. Hmm.

Actually, a pragmatic approach: provide the main JS file (the core deliverable), plus:
1. A minimal pytest test that validates the JS artifact (syntax check via node if available, structure checks) — this aligns with the pytest requirement
2. Maybe a small Python integration point (FastAPI endpoint serving the page / signaling WebSocket schema with Pydantic v2) — since guidelines emphasize Pydantic v2 typing

But I shouldn't over-deliver to the point of bloat. The core task is the JS file. Let me deliver:

1. `backend/app/static/js/webrtc_manager.js` — the main, complete, well-documented module
2. `backend/tests/static/test_webrtc_manager.py` — pytest test validating the artifact (structure, syntax via node, key API surface)
3. Optionally a small Pydantic v2 schema for signaling messages (`backend/app/schemas/webrtc.py`) to show the typed contract between JS and Python backend — this ties the JS to the Python architecture nicely

Actually, the signaling contract is important: the JS manager emits/accepts signaling messages. Defining Pydantic models for those messages (SDP offer/answer, ICE candidate, media state) makes the integration concrete and satisfies the Pydantic v2 guideline. And a pytest test can validate the JS file against the expected message types.

Let me write the JS file carefully.

Key design decisions for the JS:

```javascript
/**
 * MedIA — WebRTCManager
 * Gerenciamento de mídia local para teleconsulta (SUS/APS).
 * ...
 */
```

Events emitted:
- `devices:changed` — device list updated (plug/unplug)
- `local:stream` — local stream ready
- `remote:stream` — remote stream received
- `audio:state` / `video:state` — mute state changes
- `connection:state` — ICE/connection state changes
- `connection:quality` — periodic stats
- `error` — errors
- `audit` — audit events for LGPD/medical record logging

Constructor options:
```javascript
{
    signaling: { send(message) }, // transport abstraction
    role: 'professional' | 'patient',
    sessionId, // teleconsulta session id
    audio: true,
    video: { width: 1280, height: 720, frameRate: 30 },
    iceServers: [...STUN/TURN...],
    qualityIntervalMs: 5000,
    audioOnlyFallback: true,
    logger: console
}
```

Core methods:

1. `checkEnvironment()` — verify secure context, getUserMedia support, RTCPeerConnection support
2. `requestPermissions()` — enumerate with dummy constraints or just getUserMedia
3. `enumerateDevices()` — returns { cameras, microphones, speakers }
4. `startLocalMedia(overrides)` — getUserMedia with constraints; handle errors with typed error mapping; audio-only fallback
5. `attachLocalPreview(videoEl)` — attach stream, muted (avoid echo)
6. `toggleAudio(enabled?)` — track.enabled
7. `toggleVideo(enabled?)`
8. `switchMicrophone(deviceId)` — getUserMedia audio with deviceId, replaceTrack on senders
9. `switchCamera(deviceId)` — same for video
10. `switchSpeaker(deviceId)` — setSinkId on audio elements
11. `startScreenShare()` — getDisplayMedia, replaceTrack video sender, handle 'ended' event
12. `stopScreenShare()` — restore camera track
13. `connect()` — create RTCPeerConnection, add tracks, create offer, set local desc, send via signaling
14. `handleSignalMessage(message)` — dispatch offer/answer/candidate/bye
15. `_createPeerConnection()` — pc config, event handlers: ontrack, onicecandidate, onconnectionstatechange, oniceconnectionstatechange, onnegotiationneeded
16. Perfect negotiation pattern? For simplicity, implement polite/impolite peer handling — this is the modern robust pattern. Given medical teleconsultation, professional could be impolite peer. Let me include perfect negotiation since it's the recommended modern pattern and handles glare.
17. `getStats()` / quality monitoring — packetsLost, jitter, RTT, bitrate
18. `hangup()` / `destroy()` — stop tracks, close pc, clear intervals, emit audit

LGPD/consent: `requireConsent` option — before getUserMedia, check a consent flag; emit `consent:required` event. Keep it simple: a boolean gate + audit events.

Also important: never log sensitive data (no CNS/CPF in console logs). I'll add a note and redact session identifiers in logs.

Let me also handle:
- `devicechange` event listener for hot-plug
- Echo cancellation / noise suppression constraints (important for clinical audio quality) — default ON
- `autoGainControl: true`

Error mapping:
```javascript
const MEDIA_ERRORS = {
    NotAllowedError: 'PERMISSION_DENIED',
    NotFoundError: 'DEVICE_NOT_FOUND',
    NotReadableError: 'DEVICE_BUSY',
    OverconstrainedError: 'CONSTRAINT_UNAVAILABLE',
    SecurityError: 'INSECURE_CONTEXT',
    AbortError: 'OPERATION_ABORTED'
};
```

Perfect negotiation implementation:

```javascript
// polite peer yields on collision
async _onNegotiationNeeded() {
    try {
        this._makingOffer = true;
        await this._pc.setLocalDescription();
        this._send({ type: 'sdp', sdp: this._pc.localDescription });
    } finally {
        this._makingOffer = false;
    }
}

async _handleSdp(description) {
    const offerCollision = description.type === 'offer' && (this._makingOffer || this._pc.signalingState !== 'stable');
    this._ignoreOffer = !this._polite && offerCollision;
    if (this._ignoreOffer) return;
    
    await this._pc.setRemoteDescription(description);
    if (description.type === 'offer') {
        await this._pc.setLocalDescription();
        this._send({ type: 'sdp', sdp: this._pc.localDescription });
    }
}

async _handleCandidate(candidate) {
    try {
        await this._pc.addIceCandidate(candidate);
    } catch (err) {
        if (!this._ignoreOffer) throw err;
    }
}
```

Note: `setLocalDescription()` with no args is supported in modern browsers (implicit description). Good for "navegadores modernos".

Quality monitoring via getStats:
```javascript
async _collectQualityStats() {
    const stats = await this._pc.getStats();
    // inbound-rtp: packetsLost, jitter, bytesReceived
    // candidate-pair (nominated/selected): currentRoundTripTime
    // outbound-rtp: bytesSent
    // Compute bitrate from delta bytes / delta time
}
```

I'll compute: rtt, jitter, packets lost %, audio/video bitrate, and emit `connection:quality` with a classification (good/fair/poor) — useful for telehealth UX (show connection indicator).

Screen share with replaceTrack:
```javascript
async startScreenShare() {
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    this._screenStream = stream;
    const track = stream.getVideoTracks()[0];
    track.addEventListener('ended', () => this.stopScreenShare());
    const sender = this._videoSender;
    this._cameraTrack = sender.track; // save
    await sender.replaceTrack(track);
    this._emit('screenshare:started');
}
```

Device switching with replaceTrack (no renegotiation needed since same kind):
```javascript
async switchCamera(deviceId) {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } } });
    const track = stream.getVideoTracks()[0];
    // stop old track, replace
}
```

Careful: when switching, stop the old track to release the camera. But if screen sharing, don't replace the screen track — or stop screenshare first. I'll guard: if screen sharing, either reject or stop share first. I'll stop the share and switch.

Speaker selection: `HTMLAudioElement.setSinkId(deviceId)` — need reference to remote audio element. I'll provide `attachRemoteMedia(videoEl, audioEl)` or just use the video element for both. `setSinkId` works on video elements too. I'll keep a reference set via `setRemoteOutputElement(el)`.

Mute states: track `audioEnabled`, `videoEnabled` booleans; emit state events.

Also `hangup()` sends `{type: 'bye'}` via signaling.

Signaling abstraction: constructor takes `sendFn` or an object with `send`. The manager emits raw messages; the host app wires them to WebSocket. Also `handleSignalMessage(json)` entry point.

Message envelope (matching Pydantic schema):
```javascript
{
    type: 'sdp' | 'candidate' | 'bye' | 'media-state',
    session_id: string,
    role: 'professional' | 'patient',
    payload: { ... }
}
```

Hmm, let me define it cleanly:

```javascript
{
    kind: 'sdp' | 'ice' | 'bye' | 'state',
    session_id,
    data: ...
}
```

I'll align with the Pydantic schema I write. Let me define:

```python
class SignalKind(str, Enum):
    SDP = "sdp"
    ICE = "ice"
    BYE = "bye"
    STATE = "state"

class WebRTCSignal(BaseModel):
    kind: SignalKind
    session_id: UUID
    sender_role: Role
    payload: dict[str, Any]
    sent_at: datetime
```

And media state:
```python
class MediaState(BaseModel):
    audio_enabled: bool
    video_enabled: bool
    screen_sharing: bool
    active_mic_id: str | None
    active_camera_id: str | None
```

Quality stats:
```python
class ConnectionQuality(BaseModel):
    rtt_ms: float | None
    jitter_ms: float | None
    packets_lost_pct: float | None
    audio_kbps, video_kbps
    level: Literal['good','fair','poor']
```

Audit event:
```python
class AuditEvent(BaseModel):
    event: str
    session_id: UUID
    occurred_at: datetime
    detail: str | None
```

For the pytest test: since it's a JS artifact in a Python project, the test can:
1. Assert file exists and is non-empty
2. If node is available, run `node --check` for syntax validation
3. Parse the file text to assert presence of key methods (getUserMedia, RTCPeerConnection, replaceTrack, setSinkId, etc.)
4. Optionally, if node available, load the class in a VM with mocked navigator and test logic? That's heavy. A smoke test with mocked `navigator.mediaDevices` and `RTCPeerConnection` in Node could actually work since the class doesn't strictly need a browser at construction time. Let me consider: constructor stores options; `enumerateDevices` uses navigator.mediaDevices. In Node, I can inject globals. Using `vm.runInNewContext` with a sandbox containing mocked navigator, RTCPeerConnection, window, document... That could be a nice functional test. But it adds fragility. I'll do a middle ground: syntax check + API surface assertions + a small sandboxed smoke test if node exists (skip otherwise with pytest.mark.skipif).

Actually, let me write a functional test using Node's `vm` module: load the JS, instantiate WebRTCManager with mocked navigator.mediaDevices (enumerateDevices, getUserMedia returning fake tracks), mocked RTCPeerConnection, and test: toggleAudio, toggleVideo, event emission, message building. Fake tracks: `{ kind, enabled: true, stop(), addEventListener() }`. Fake stream: `{ getTracks(), getVideoTracks(), getAudioTracks() }`. RTCPeerConnection mock: methods used — constructor(config), addTrack, createOffer? Actually with implicit setLocalDescription I still call pc.setLocalDescription() — mock it. addEventListener, signalingState getter, etc.

This is doable but the mock surface needs to match exactly what the JS touches. Let me be careful to keep the JS's browser API usage enumerable and write mocks accordingly. Risk: subtle mismatch → test fails. I'll write the JS first, then carefully write mocks covering every API touched in the tested paths.

Tested paths (keep minimal):
- constructor + `on/emit`
- `enumerateDevices()` with mocked navigator.mediaDevices.enumerateDevices
- `toggleAudio(true/false)` — needs local stream set. I can set `manager._localStream = fakeStream` directly? Accessing private from test is meh but acceptable for JS smoke test. Better: call `startLocalMedia()` with mocked getUserMedia. That path: checkEnvironment (needs secure context flag — mock `window.isSecureContext = true`, navigator.mediaDevices exists), consent gate (set requireConsent false or consentGiven true), getUserMedia returns fake stream, attach preview skipped (no element), emit local:stream, start devicechange listener (navigator.mediaDevices.addEventListener — mock). Then toggleAudio works.
- `buildStateMessage()` / `_send` capture: pass a `send` spy in signaling and assert envelope shape matches Pydantic schema fields (kind, session_id, sender_role, payload).

That's a solid smoke test. Also test error mapping: getUserMedia rejecting with NotAllowedError → emits error with code PERMISSION_DENIED.

Node availability: `shutil.which('node')`. skipif not found.

Also `node --check` for syntax: run subprocess `node --check file`. Good.

Now, the Pydantic schemas file — should I include it? The task says "crie backend/app/static/js/webrtc_manager.js". The primary deliverable is that file. The guidelines mention Pydantic v2 etc. I think including a compact signaling schema module + the pytest test makes the deliverable complete and architecture-compliant without bloating. I'll include:

1. `backend/app/static/js/webrtc_manager.js` (main)
2. `backend/app/schemas/webrtc.py` (Pydantic v2 signaling contract)
3. `backend/tests/static/test_webrtc_manager.py` (pytest)

Maybe also a tiny FastAPI router for signaling WebSocket? That might be over-delivery. The task is specifically the JS module. I'll keep the schema (contract) + test, and mention integration points briefly. Actually, a minimal WebSocket signaling endpoint would make it genuinely usable... but the task says "Módulo WebRTC de Gerenciamento de Mídia Local" — local media management. The RTCPeerConnection handling is included but signaling transport is abstracted. I'll skip the WS endpoint to stay focused, but the schema file documents the contract. Hmm, or I could include a very compact signaling router. Let me weigh: response length matters. The JS file itself will be ~600-800 lines with docs. Adding schema (~80 lines) + test (~200 lines) is reasonable. A WS router would add another ~100 lines. I'll skip the router and note it as integration point. Actually the user