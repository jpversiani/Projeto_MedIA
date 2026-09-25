All 14 tests pass. The file `backend/app/static/js/webrtc_manager.js` already exists with a complete `WebRTCManager` class that satisfies every test criterion:

- **Export**: `export class WebRTCManager extends EventTarget` (ES module, no globals)
- **getUserMedia**: clinical audio profile (`echoCancellation`, `noiseSuppression`, `autoGainControl`), video (`width`, `height`, `frameRate`), `deviceId: { exact: ... }`
- **Consent**: `registrarConsentimento` + `#consentimentoRegistrado` guard + LGPD
- **Dynamic device selection**: `enumerateDevices`, `alternarMicrofone`, `alternarCamera`, `listarDispositivos`, `devicechange` listener
- **Mute/unmute**: `alternarMuteAudio`, `definirMuteAudio`, `alternarMuteVideo` via `track.enabled = !`
- **RTCPeerConnection**: `createOffer`, `createAnswer`, `setLocalDescription`, `setRemoteDescription`, `addIceCandidate`, `onicecandidate`, `ontrack`, `onconnectionstatechange`, `connectionState`, STUN/TURN ICE servers
- **replaceTrack**: `getSenders()` + `replaceTrack()` for hotplug without renegotiation
- **ICE**: `adicionarCandidatoRemota` checks `remoteDescription`
- **SUS/APS/LGPD**: `cns`/`cpf` local-only, no interpolation in SDP/ICE
- **No MediaRecorder**, structural balance, no invalid APIs
- **fechar()**: `.stop()` + `.close()`

The implementation is complete and all tests pass (`14 passed`).