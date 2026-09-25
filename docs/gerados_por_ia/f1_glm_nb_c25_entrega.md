The user wants me to create a WebRTC media management module for a medical teleconsultation project (Projeto MedIA). The task is specifically to create `backend/app/static/js/webrtc_manager.js` with a `WebRTCManager` class that handles:

1. getUserMedia capture
2. Dynamic microphone/camera selection
3. Mute/unmute controls
4. RTCPeerConnection manipulation for medical teleconsultation in modern browsers

The guidelines mention Python 3.12, Pydantic v2, SQLAlchemy 2.0, SUS/APS standards (CIAP-2, CID-10, SOAP method, CNS/CPF identification), and pytest test coverage. However, the actual deliverable is a JavaScript file. The Python guidelines are part of the project architecture context, but the specific task is the JS module. I should focus on the JavaScript file as the primary deliverable, but I can note how it integrates with the Python backend (e.g., signaling via WebSocket endpoints).

Since the task is JavaScript, I should write high-quality, modern JavaScript (ES2020+) with:
- JSDoc typing (since JS doesn't have strict typing, but I can use JSDoc annotations for documentation)
- Class `WebRTCManager`
- getUserMedia with device enumeration
- Dynamic device selection (microphone/camera switching, including hot-plug via devicechange event)
- Mute/unmute for audio and video (track.enabled toggling)
- RTCPeerConnection management: offer/answer, ICE candidates, renegotiation
- Signaling abstraction (callbacks or a signaling interface that the backend WebSocket provides)
- Medical context: teleconsulta — maybe include consent handling (LGPD compliance for Brazilian healthcare), quality adaptation, secure context checks (HTTPS required for getUserMedia)
- Error handling with meaningful error codes
- Event emitter pattern for integration

I should also consider:
- Browser compatibility: modern browsers (Chrome, Firefox, Safari, Edge). Use `navigator.mediaDevices` with fallback checks.
- `navigator.mediaDevices.ondevicechange` for hot-plug
- Permission handling and permission state via `navigator.permissions.query`
- FacingMode for mobile
- Ideal/constraints vs exact
- Screen sharing (getDisplayMedia) could be a bonus for teleconsulta (sharing exam results)
- ICE servers configuration (STUN/TURN)
- Connection state monitoring, ICE connection state, restart ICE on failure
- Stats collection for quality monitoring (optional but useful)
- Cleanup/dispose properly

For the medical context (SUS/APS):
- LGPD compliance: consent before capture, no local recording without consent
- Secure context requirement (HTTPS) — getUserMedia requires it
- Audit logging hooks (without storing PHI in logs)
- CNS/CPF are backend concerns, but I can mention session identification hooks

I should also provide:
- A brief integration example (HTML usage)
- Maybe a small pytest note? The guidelines say pytest coverage, but for JS we'd use Jest. I could mention that the signaling contract is tested via pytest on the backend side, and provide a minimal example of how the backend signaling endpoint contract looks (FastAPI WebSocket). But the task says "crie backend/app/static/js/webrtc_manager.js" — the main deliverable is the JS file. I'll focus on that, and add a concise integration section showing the FastAPI WebSocket signaling contract so the JS connects properly, plus optionally a small pytest test for the signaling schema with Pydantic v2 to align with the architecture guidelines.

Actually, let me re-read: "Execute com precisão conforme as diretrizes." The guidelines include Python typing, SUS/APS standards, and pytest coverage. The primary artifact is the JS file. To honor the guidelines without bloating, I can:

1. Deliver the complete `webrtc_manager.js` (main artifact).
2. Provide a minimal Pydantic v2 signaling schema (`backend/app/schemas/webrtc.py`) that defines the message contract — this ties the JS to the backend with strict typing.
3. Provide a small pytest test for the schema validation.

That gives a coherent, integrated deliverable. But I must be careful not to overreach — the task is the JS module. I'll make the JS file the star, and add the signaling contract + test as supporting artifacts since the guidelines demand pytest coverage and Pydantic v2 typing. Keep those concise.

Let me design the WebRTCManager class:

```javascript
/**
 * WebRTCManager — Gerenciamento de mídia local para teleconsulta (Projeto MedIA)
 * ...
 */
```

Key features:

1. **Constructor options**: 
   - `signaling` — object with `send(message)` and event dispatch, or callbacks: `onLocalOffer`, `onLocalAnswer`, `onLocalIceCandidate`, etc. Better: the manager exposes an event emitter; the app wires signaling.
   - `iceServers` — RTCIceServer[]
   - `audioDeviceId`, `videoDeviceId`, defaults
   - `resolution` presets
   - callbacks: `onLocalStream`, `onRemoteStream`, `onDeviceListChanged`, `onConnectionStateChange`, `onError`, `onStats`

2. **Methods**:
   - `async init()` — enumerate devices, check secure context
   - `async requestPermissions()` — optional pre-permission with dummy constraints
   - `async startLocalStream(constraints?)` — getUserMedia
   - `async switchMicrophone(deviceId)` — replaceTrack or renegotiate
   - `async switchCamera(deviceId)`
   - `async toggleAudioMute()` / `setAudioMuted(bool)` / `isAudioMuted`
   - `async toggleVideoMute()` / `setVideoMuted(bool)`
   - `async startCall()` / `createOffer()`
   - `async handleSignalMessage(message)` — process offer/answer/candidate from remote
   - `async createPeerConnection()` — internal
   - `async replaceTrack(kind, track)` — uses RTCRtpSender.replaceTrack to avoid renegotiation
   - `async restartIce()` — RTCPeerConnection.restartIce() or ICE restart via offer
   - `async startScreenShare()` / `stopScreenShare()` — getDisplayMedia (bonus for sharing exam documents)
   - `getStats()` — periodic stats (bitrate, packets lost, RTT)
   - `async hangUp()` / `dispose()` — cleanup
   - `handleDeviceChange` — devicechange listener, re-enumerate, handle active device removal

3. **Events**: use a simple EventTarget-based or custom emitter. Modern approach: extend EventTarget and dispatch CustomEvents. That's clean and native.

4. **Error taxonomy**: custom error class `WebRTCManagerError` with codes like `SECURE_CONTEXT_REQUIRED`, `PERMISSION_DENIED`, `DEVICE_NOT_FOUND`, `NOT_SUPPORTED`, `SIGNALING_ERROR`, etc. Map `DOMException` names (NotAllowedError, NotFoundError, NotReadableError, OverconstrainedError, AbortError, SecurityError) to friendly codes — important for teleconsulta UX (e.g., guiding patient to allow camera).

5. **Medical/LGPD considerations**:
   - Consent gate: `requireConsent` option — before starting capture, fires `consent:request` event and waits for `grantConsent()` (LGPD Art. 7/11 — sensitive health data). Actually simpler: expose `consentGranted` flag that must be set before `startLocalStream` if `requireConsent: true`. Or emit event and await a promise. I'll implement: option `onConsentRequest: async () => boolean` — if provided, called before capture; if returns false, abort. Clean and testable.
   - No PHI in logs: logger redacts device labels? Device labels can be considered low-sensitivity but let's add a `debug` mode flag; default logs don't include labels.
   - `data-channel` for chat/vitals? Could add optional reliable data channel for text (e.g., sending SOAP notes snippets or chat). Maybe include a simple data channel helper `sendDataChannelMessage` — useful for teleconsulta (chat, signals). I'll include it as optional lightweight feature.

6. **Renegotiation handling**: perfect negotiation pattern (polite/impolite peers) — this is the modern standard for glare handling. Implement with `polite` flag determined by role or by comparing IDs. I'll implement the Perfect Negotiation pattern (from W3C/mozilla docs) since it's the robust modern approach.

7. **Codec preferences**: prefer VP8/H264? Could set via `RTCRtpTransceiver.setCodecPreferences` — maybe optional; keep simple but mention. I might include a light preference for opus/VP8 to maximize compatibility. Actually to keep code focused, I'll skip codec preference or add minimal.

8. **Adaptive quality**: `setBandwidthProfile`? Could apply `sender.setParameters` with maxBitrate. Include a simple `setVideoQuality({ maxBitrate, frameRate, resolution })` that applies encoding params and, if needed, applies constraints to track. Good for teleconsulta on poor connections (common in APS rural areas).

Let me now write the code carefully.

Structure of the JS file:

```javascript
'use strict';

/**
 * =============================================================================
 * Projeto MedIA — Módulo WebRTC de Gerenciamento de Mídia Local (C25)
 * =============================================================================
 * ...
 */

// Constants
const DEFAULT_ICE_SERVERS = [...stun...];

// Error codes enum (frozen object)
const ErrorCodes = Object.freeze({...});

class WebRTCManagerError extends Error {
  constructor(code, message, cause) { ... }
}

// Signal message types enum
const SignalType = Object.freeze({ OFFER:'offer', ANSWER:'answer', CANDIDATE:'candidate', BYE:'bye', ICE_RESTART:'ice_restart' });

class WebRTCManager extends EventTarget {
  constructor(options = {}) {...}
  
  // --- lifecycle
  async init()
  async startLocalStream(overrides)
  async stopLocalStream()
  
  // --- devices
  async enumerateDevices()
  async switchAudioDevice(deviceId)
  async switchVideoDevice(deviceId)
  _handleDeviceChange()
  
  // --- mute controls
  setAudioMuted(muted)
  toggleAudioMuted()
  setVideoMuted(muted)
  toggleVideoMuted()
  
  // --- peer connection / negotiation
  async createPeerConnection()
  async call() // create offer and send
  async handleSignalMessage(msg)
  async _onNegotiationNeeded()
  async _createOffer/_createAnswer...
  async restartIce()
  
  // --- tracks
  async _replaceTrack(kind, newTrack)
  
  // --- screen share
  async startScreenShare()
  async stopScreenShare()
  
  // --- data channel
  _setupDataChannel()
  sendDataChannelMessage(obj)
  
  // --- stats
  async getStatsSnapshot()
  _startStatsPolling() / _stopStatsPolling()
  
  // --- quality
  async setVideoQuality({maxBitrate, frameRate, height})
  
  // --- teardown
  async hangUp()
  dispose()
  
  // --- helpers
  _emit(type, detail)
  _log(...)
  get #state...
}
```

Perfect negotiation: I'll implement with `polite` boolean option. The signaling server assigns roles or we compare peer UUIDs. I'll accept `polite` in options and also support `determineRole` via signaling. Keep it: `options.polite` boolean, default false; document that backend assigns.

Signal message handling: `handleSignalMessage({ type, payload })` where type in offer/answer/candidate/bye. The manager emits `signal:out` events with `{ type, payload }` that the app forwards to the WebSocket. This decouples from transport.

Let me write the actual code now, being careful with correctness:

- `navigator.mediaDevices` check: if undefined → either not secure context or unsupported. Check `window.isSecureContext`.
- `enumerateDevices` before permission returns devices with empty labels — handle by filtering/knowing this.
- Device change: `navigator.mediaDevices.addEventListener('devicechange', ...)`. Debounce it.
- Switching device: preferred approach — get new stream with exact deviceId, then `sender.replaceTrack(newTrack)` to avoid renegotiation; stop old track. If no peer connection yet, just update local stream: remove old track, add new track, and if stream attached to <video>, the app re-attaches; we emit `localstream:changed`.
- Mute: `track.enabled = false` — standard. Emit events `audio:muted` etc. Note: muted video track still sends black frames; alternative is removing track — but enabled=false is standard and keeps connection alive.
- getUserMedia constraints: use `deviceId: exact` when switching (user explicitly chose), `ideal` on first start. Also `echoCancellation`, `noiseSuppression`, `autoGainControl` defaults true for teleconsulta clarity.
- OverconstrainedError handling: fallback to ideal and retry.
- Screen share: `getDisplayMedia({ video: true, audio: false })`, replace video track with screen track, listen for track `ended` (user stops sharing via browser UI) to revert to camera.
- Stats: parse `getStats()` reports for outbound video: bytesSent delta → bitrate, packetsLost, roundTripTime; inbound for remote. Provide snapshot object.
- ICE restart: `pc.restartIce()` triggers negotiationneeded; in perfect negotiation, handle. Also explicit `iceRestart: true` offer fallback.
- Connection state monitoring: `pc.onconnectionstatechange` → emit events; on 'failed' → auto `restartIce()` (with attempt limit and backoff).
- Data channel: create on polite/impolite? Only one side creates: the caller (impolite/caller) creates with `pc.createDataChannel('mediia-control', { ordered: true })`; the other side receives via `ondatachannel`. Provide `sendControlMessage`.
- Cleanup: stop all tracks, close pc, remove listeners, clear timers.

Also add `attachLocalPreview(videoEl)` helper? Maybe useful but the app can do it. I'll include small helpers `attachStream(videoElement, stream)` as static utility — nice DX. Keep minimal.

JSDoc types throughout. Use `@typedef` for options and signal messages.

Now the backend contract (Pydantic v2 schema) — small file `backend/app/schemas/webrtc.py`:

```python
from __future__ import annotations
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator
...

class SDPBase(BaseModel):
    sdp: str = Field(min_length=1)
    ...
```

Actually the JS emits `{ type: 'offer'|'answer'|'candidate'|'bye', payload: {...} }`. Payload for offer/answer: `{ sdp: RTCSessionDescriptionInit-like { type, sdp } }`? Let me define: the emitted message is `{ type, payload }` where:
- offer/answer: payload = `{ sdp: string, type: 'offer'|'answer' }` — hmm redundant. Simpler: payload for offer/answer is the session description `{ type, sdp }`; the outer `type` is the message kind. To avoid confusion, message: `{ kind: 'sdp'|'ice'|'bye', ... }`? Let me define clean:

Outgoing/incoming signal envelope:
```json
{ "type": "offer", "sdp": "v=0...", "rid": "<consultaid>" }
{ "type": "answer", "sdp": "..." }
{ "type": "candidate", "candidate": "...", "sdpMid": "0", "sdpMLineIndex": 0, "usernameFragment": "..." }
{ "type": "bye" }
```

So `handleSignalMessage` accepts this flat shape; `_emit('signal:out', detail)` emits the same flat shape. That's simple and matches typical WebSocket signaling. The Pydantic schema models this with discriminated union:

```python
class OfferMessage(BaseModel):
    type: Literal["offer"]
    sdp: str
class AnswerMessage(BaseModel):
    type: Literal["answer"]
    sdp: str
class CandidateMessage(BaseModel):
    type: Literal["candidate"]
    candidate: str
    sdpMid: str | None = None
    sdpMLineIndex: int | None = Field(default=None, ge=0)
    usernameFragment: str | None = None
class ByeMessage(BaseModel):
    type: Literal["bye"]

SignalIn = Annotated[Union[...], Field(discriminator="type")]
```

And a session context model with CNS masking (LGPD): `CnsRef` with validation + `masked_cns` helper. CNS validation algorithm (1st digits: 1,2 for regular, 7,8,9 for cards). Implement CNS validation: 15 digits; for starting with 1 or 2: sum with weights 15..2 mod 11 == 0; for 7/8/9: different algorithm (mod 11 with weights, check DV). I can implement the standard CNS validation. That ties to "identificação por CNS/CPF" guideline. Keep it compact.

And a pytest test file `backend/tests/test_webrtc_schemas.py` testing valid/invalid CNS, signal messages, bye. Keep concise.

Also maybe a tiny FastAPI WebSocket endpoint example? That might be too much. I'll include a very compact example in the docstring or in the answer text showing wiring. Actually, to keep the response focused, I'll include: (1) the JS file (main), (2) the Pydantic schema file (contract), (3) pytest test, (4) short usage/integration snippet. That satisfies "conformidade total e cobertura de testes" in a proportionate way.

Let me now write the JS in full detail. I need to be meticulous about correctness.

```javascript
'use strict';

/**
 * ============================================================================
 *  Projeto MedIA — Módulo WebRTC de Gerenciamento de Mídia Local (C25)
 * ============================================================================
 *  Classe `WebRTCManager` responsável por:
 *    - Captura de mídia local via getUserMedia (áudio/vídeo);
 *    - Enumeração e seleção dinâmica de microfones/câmeras (com hot-plug);
 *    - Controle de mute/unmute de áudio e vídeo;
 *    - Gerenciamento de RTCPeerConnection (Perfect Negotiation, ICE restart,
 *      replaceTrack, canal de dados e coleta de estatísticas);
 *    - Compartilhamento de tela (getDisplayMedia) para exibição de exames.
 *
 *  Conformidade:
 *    - LGPD (Lei 13.709/2018): captura condicionada a consentimento explícito
 *      (art. 11 — dados sensíveis de saúde); nenhum dado pessoal (PHI) é
 *      registrado em logs; labels de dispositivos só em modo debug.
 *    - Requer contexto seguro (HTTPS/localhost) — exigência do getUserMedia.
 *    - Padrões SUS/APS: teleconsulta como ação estratégica (e-SUS APS, RNDS).
 *
 *  Navegadores suportados (modernos, evergreen):
 *    Chrome/Edge ≥