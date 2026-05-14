# Mobile Debugging Guide

> Use este arquivo quando o problema ainda não está caracterizado e você precisa descobrir onde está a falha.
> Ele é útil para separar bug de rede, UI, permissão, crash nativo ou lifecycle antes de corrigir qualquer coisa.

---

## Quick Start

- Abra este arquivo quando o bug parece “mobile-only”, intermitente ou difícil de reproduzir no simulador.
- Extraia daqui: sintoma principal, evidência necessária e ferramenta que confirma a hipótese.
- Se o problema já é claramente de performance, use `mobile-performance.md`. Se já é de API, cruze com `mobile-backend.md`.

## Jump Map

| Sintoma | Vá para | Colete |
| --- | --- | --- |
| app crasha ou fecha | `## 2. Common Debugging Workflows` | stack trace, logs nativos e contexto de reprodução |
| request falha | `### "API Request Failed" (Network)` | payload, headers, proxy e estado de conectividade |
| UI laggy | `### "The UI is Laggy" (Performance)` | FPS, profiler e tipo de interação |
| permissão falha | `## Symptom Triage` | OS, prompt, denial path e retorno por settings |
| app volta quebrado do background | `## Symptom Triage` | lifecycle event, subscriptions e state restore |

## Symptom Triage

- crash: confirme se a falha é JS, bridge ou nativa antes de tocar em código
- request falhando: compare conectividade, SSL/proxy, token e versionamento do app
- UI laggy: isole se o gargalo é lista, animação, imagem ou memory leak
- permission issue: registre a primeira negação, rationale e retorno por settings
- resume/background bug: colete logs de lifecycle, subscriptions e rehydration

## 1. Mobile Debugging Mindset

```
Web Debugging:      Mobile Debugging:
┌──────────────┐    ┌──────────────┐
│  Browser     │    │  JS Bridge   │
│  DevTools    │    │  Native UI   │
│  Network Tab │    │  GPU/Memory  │
└──────────────┘    │  Threads     │
                    └──────────────┘
```

**Key Differences:**

1.  **Native Layer:** JS code works, but app crashes? It's likely native (Java/Obj-C).
2.  **Deployment:** You can't just "refresh". State gets lost or stuck.
3.  **Network:** SSL Pinning, proxy settings are harder.
4.  **Device Logs:** `adb logcat` and `Console.app` are your truth.

---

## 2. Common Mobile Debugging Anti-Patterns

| ❌ Default               | ✅ Mobile-Correct                          |
| ------------------------ | ------------------------------------------ |
| "Add console.logs"       | Use Flipper / Reactotron                   |
| "Check network tab"      | Use Charles Proxy / Proxyman               |
| "It works on simulator"  | **Test on Real Device** (HW specific bugs) |
| "Reinstall node_modules" | **Clean Native Build** (Gradle/Pod cache)  |
| Ignored native logs      | Read `logcat` / Xcode logs                 |

---

## 1. The Toolset

### ⚡ React Native & Expo

| Tool           | Purpose           | Best For           |
| -------------- | ----------------- | ------------------ |
| **Reactotron** | State/API/Redux   | JS side debugging  |
| **Flipper**    | Layout/Network/db | Native + JS bridge |
| **Expo Tools** | Element inspector | Quick UI checks    |

### 🛠️ Native Layer (The Deep Dive)

| Tool             | Platform | Command        | Why Use?                  |
| ---------------- | -------- | -------------- | ------------------------- |
| **Logcat**       | Android  | `adb logcat`   | Native crashes, ANRs      |
| **Console**      | iOS      | via Xcode      | Native exceptions, memory |
| **Layout Insp.** | Android  | Android Studio | UI hierarchy bugs         |
| **View Insp.**   | iOS      | Xcode          | UI hierarchy bugs         |

---

## 2. Common Debugging Workflows

### 🕵️ "The App Just Crashed" (Red Screen vs Crash to Home)

**Scenario A: Red Screen (JS Error)**

- **Cause:** Undefined is not an object, import error.
- **Fix:** Read the stack trace on screen. It's usually clear.

**Scenario B: Crash to Home Screen (Native Crash)**

- **Cause:** Native module failure, memory OOM, permission usage without declaration.
- **Tools:**
  - **Android:** `adb logcat *:E` (Filter for Errors)
  - **iOS:** Open Xcode → Window → Devices → View Device Logs

> **💡 Pro Tip:** If app crashes immediately on launch, it's almost 100% a native configuration issue (Info.plist, AndroidManifest.xml).

### 🌐 "API Request Failed" (Network)

**Web:** Open Chrome DevTools → Network.
**Mobile:** _You usually can't see this easily._

**Solution 1: Reactotron/Flipper**

- View network requests in the monitoring app.

**Solution 2: Proxy (Charles/Proxyman)**

- **Hard but powerful.** See ALL traffic even from native SDKs.
- Requires installing SSL cert on device.

### 🐢 "The UI is Laggy" (Performance)

**Don't guess.** measure.

- **React Native:** Performance Monitor (Shake menu).
- **Android:** "Profile GPU Rendering" in Developer Options.
- **Issues:**
  - **JS FPS drop:** Heavy calculation in JS thread.
  - **UI FPS drop:** Too many views, intricate hierarchy, heavy images.

---

## 3. Platform-Specific Nightmares

### Android

- **Gradle Sync Fail:** Usually Java version mismatch or duplicate classes.
- **Emulator Network:** Emulator `localhost` is `10.0.2.2`, NOT `127.0.0.1`.
- **Cached Builds:** `./gradlew clean` is your best friend.

### iOS

- **Pod Issues:** `pod deintegrate && pod install`.
- **Signing Errors:** Check Team ID and Bundle Identifier.
- **Cache:** Xcode → Product → Clean Build Folder.

---

## 📝 DEBUGGING CHECKLIST

- [ ] **Is it a JS or Native crash?** (Red screen or home screen?)
- [ ] **Did you clean build?** (Native caches are aggressive)
- [ ] **Are you on a real device?** (Simulators hide concurrency bugs)
- [ ] **Did you check the native logs?** (Not just terminal output)

> **Remember:** If JavaScript looks perfect but the app fails, look closer at the Native side.
