# Agent Workspace Developer Guide

This guide covers the three integration approaches for extending the Amazon Connect agent workspace, plus the full SDK API reference.

---

## Agent Workspace Overview

The Amazon Connect agent workspace is a browser-based application that provides agents with a unified interface for handling customer interactions. It embeds the Contact Control Panel (CCP), step-by-step guides, Customer Profiles, Cases, and AI-powered agent assist tools into a single workspace shell.

Applications load inside iframes within the workspace shell. The workspace manages authentication, theming, and event routing between all embedded applications.

There are three types of integrations:

- **Third-party applications (3P apps)**: Custom web applications with a visible UI that appear as tabs in the workspace.
- **Third-party services (headless)**: Background processes with no visible UI that run for the entire agent session.
- **AWS-managed applications**: Built-in applications managed by AWS (Customer Profiles, Cases, etc.).

Agent workspace URL: `https://{instance-alias}.my.connect.aws/agent-app-v2/`

---

## Best Practices

- **Embedding security**: Use `X-Frame-Options` and CSP headers to ensure your app can only be embedded in the Connect workspace. Restrict `frame-ancestors` to the Connect domain.
- **Multiple domains**: Register all domains (including staging and localhost for development) as approved origins via the `AssociateApprovedOrigin` API.
- **Streams initialization**: Initialize the Streams JS library before creating SDK clients. Do not call `initCCP` multiple times — it should be called once on page load.
- **Accessibility**: Follow WCAG 2.1 AA guidelines. Use semantic HTML elements, ARIA labels, and ensure full keyboard navigation support.
- **Theming**: Always use `app.getTheme()` to match the workspace theme. Subscribe to `onThemeChanged` for dynamic updates when agents toggle dark mode.

---

## A. Third-Party Applications (3P Apps)

Third-party applications are custom web applications loaded inside the agent workspace via HTTPS iframes. They appear as tabs and interact with the workspace through the Amazon Connect SDK.

### Prerequisites — IAM Role

An IAM role with the following permissions is required to register and manage third-party applications:

- `app-integrations:CreateApplication`
- `connect:AssociateApprovedOrigin`

In the AWS console, register your application under the Amazon Connect admin console > "Third-party applications."

### Prerequisites

- HTTPS-hosted web application (HTTP is rejected by the iframe sandbox).
- Application registered in the Amazon Connect console under "Third-party applications."
- `@amazon-connect/sdk` packages installed.

### Create Your Application

1. Go to the Amazon Connect admin console and navigate to "Third-party applications."
2. Register your app: provide a name, namespace, and origin URL (must be HTTPS).
3. Configure permissions: select which agent data the app can access (contacts, agent state, etc.).
4. Associate the app with a security profile to control which agents see it in their workspace.

### Installation

```bash
npm install @amazon-connect/contact @amazon-connect/core
```

Additional SDK packages by feature:

```bash
npm install @amazon-connect/agent        # Agent state, routing profile
npm install @amazon-connect/voice        # Voice call controls
npm install @amazon-connect/email        # Email handling
npm install @amazon-connect/file         # File upload/download
npm install @amazon-connect/message-template  # Message templates
npm install @amazon-connect/quick-responses   # Quick responses
npm install @amazon-connect/app-controller    # App lifecycle management
```

### Initialization

```typescript
import { AmazonConnectApp } from "@amazon-connect/core";

const app = await AmazonConnectApp.init({
  instanceUrl: "https://my-instance.my.connect.aws",
  // Optional: specify container element for embedded mode
});

// The app is now connected to the workspace
// All SDK clients use this app instance
```

The `init()` call establishes a secure communication channel between the iframe and the parent workspace window via `postMessage`. It performs:

1. Origin validation against the registered allowed origins.
2. Authentication handshake (the workspace passes auth context to the app).
3. Theme synchronization (the app receives the current workspace theme).
4. Event channel setup for bidirectional communication.

### Authentication Support

The workspace provides authentication context to 3P apps:

```typescript
import { AmazonConnectApp } from "@amazon-connect/core";

const app = await AmazonConnectApp.init({ instanceUrl });

// Access authenticated user info
const user = app.getUser();
console.log(user.getLanguage()); // Agent's language preference
```

Apps do not need to implement their own login flow when running inside the workspace -- the workspace session is shared. For apps that also run standalone (outside the workspace), implement a fallback auth flow.

### Theme Integration

Apps receive the workspace theme and can adapt their UI:

```typescript
import { AmazonConnectApp } from "@amazon-connect/core";

const app = await AmazonConnectApp.init({ instanceUrl });

// Get current theme
const theme = app.getTheme();
// theme.primaryColor, theme.backgroundColor, etc.

// Listen for theme changes (e.g., user switches dark mode)
app.onThemeChanged((newTheme) => {
  applyTheme(newTheme);
});
```

### Lifecycle Events

```typescript
// App is being closed/hidden
app.onDestroy(() => {
  // Cleanup resources, save state
});

// App gained focus
app.onFocus(() => {
  // Refresh data, update UI
});

// App lost focus
app.onBlur(() => {
  // Pause animations, reduce polling
});
```

### Error Handling

```typescript
try {
  const app = await AmazonConnectApp.init({ instanceUrl });
} catch (error) {
  if (error.code === "ORIGIN_NOT_ALLOWED") {
    console.error("App origin not registered in Connect console");
  } else if (error.code === "INSTANCE_UNREACHABLE") {
    console.error("Cannot reach Connect instance");
  } else if (error.code === "AUTH_FAILED") {
    console.error("Authentication handshake failed");
  }
}
```

### SDK Without Package Manager (Bundling Guide)

When npm is not available (e.g., legacy apps, static sites), you can bundle the SDK packages into a single file:

1. Create a build project:
   ```bash
   mkdir connect-sdk-build && cd connect-sdk-build
   ```
2. Initialize the project:
   ```bash
   npm init -y
   ```
3. Install SDK packages:
   ```bash
   npm install @amazon-connect/contact @amazon-connect/agent @amazon-connect/core @amazon-connect/app-controller
   ```
4. Install a bundler:
   ```bash
   npm install --save-dev esbuild
   ```
5. Create an entry file (`index.js`):
   ```javascript
   export { ContactClient } from "@amazon-connect/contact";
   export { AgentClient } from "@amazon-connect/agent";
   export { AmazonConnectApp } from "@amazon-connect/core";
   export { AppControllerClient } from "@amazon-connect/app-controller";
   ```
6. Add a build script to `package.json`:
   ```json
   {
     "scripts": {
       "build": "esbuild index.js --bundle --outfile=dist/amazon-connect-sdk.js --format=iife --global-name=AmazonConnectSDK"
     }
   }
   ```
7. Build:
   ```bash
   npm run build
   ```
8. Copy `dist/amazon-connect-sdk.js` to your project.

Usage in HTML:

```html
<script src="amazon-connect-sdk.js"></script>
<script>
  const { ContactClient, AgentClient } = window.AmazonConnectSDK;
</script>
```

StreamsJS integration: Load Streams JS first (`connect-streams.js`), then the SDK bundle. Initialize CCP via `connect.core.initCCP()`, then create SDK clients.

### Agent Data Integration

Use the Agent Client to subscribe to agent state and retrieve role/queue information for your app:

- Subscribe to agent state changes: `agentClient.onStateChanged(callback)`
- Get agent routing profile: `agentClient.getRoutingProfile()`
- Get available states: `agentClient.listAvailabilityStates()`
- Use case: show agent-specific data in your app based on their assigned queues or role.

### Events and Requests Pattern

The SDK uses two communication patterns between the workspace and your app:

- **Events**: workspace-to-app notifications (agent state changed, contact incoming, theme changed). Events use a subscribe/unsubscribe pattern with `on*` / `off*` methods.
- **Requests**: app-to-workspace actions (set agent state, accept contact, launch another app). Requests use async methods that return promises.

```typescript
// Event pattern: subscribe to notifications
contactClient.onIncoming((event) => {
  console.log("New contact:", event.contactId);
});

// Request pattern: perform an action
await contactClient.accept(contactId);
```

### Troubleshooting

**Events not received:**
- Verify the app origin is registered in the Connect console (exact match, including protocol and port).
- Check browser console for `postMessage` origin errors.
- Ensure `AmazonConnectApp.init()` completed successfully before subscribing to events.

**Requests failing:**
- Confirm the agent's security profile grants permissions for the requested resource.
- Check that the SDK package version matches the Connect instance version.
- Look for CORS errors if the app makes direct API calls.

**Testing locally:**
- Use `https://localhost:{port}` (not `http://`).
- Register `https://localhost:{port}` as an allowed origin in the Connect console.
- Use a valid SSL certificate (self-signed works with browser exceptions).

**Testing deployed:**
- Register the production domain as an allowed origin.
- Verify the app loads in a standalone browser tab before testing inside the workspace.
- Check the browser network tab for blocked requests or failed resource loads.

---

## B. Third-Party Services (Headless)

Third-party services are background processes that run for the duration of the agent's workspace session. They have no visible UI -- they execute logic in response to workspace events.

### Use Cases

- **Auto-launch apps on ACW** -- listen for the ACW event and programmatically launch a specific 3P app.
- **Custom auth flows** -- perform additional authentication steps when the agent logs in.
- **Contact event listeners** -- log contact events to an external system, trigger webhooks, or update external CRM records.
- **App focus control** -- automatically switch focus to a specific app when a contact arrives.
- **Background data sync** -- periodically sync data between the workspace and an external system.

### Service Setup

1. In the Amazon Connect console, navigate to "Third-party applications."
2. Create a new application with the "Service" type (not "Application").
3. Provide the HTTPS URL of the service endpoint.
4. The service URL is loaded in a hidden iframe -- no UI is rendered.
5. The service initializes via the same `AmazonConnectApp.init()` flow and subscribes to events.

### Example: Auto-Launch App on ACW

```typescript
import { AmazonConnectApp } from "@amazon-connect/core";
import { ContactClient } from "@amazon-connect/contact";
import { AppControllerClient } from "@amazon-connect/app-controller";

const app = await AmazonConnectApp.init({ instanceUrl });
const contactClient = new ContactClient(app);
const appController = new AppControllerClient(app);

// Listen for ACW state
contactClient.onStartingAcw((event) => {
  // Auto-launch the disposition app
  appController.launch({
    appId: "disposition-app-id",
    contactId: event.contactId,
  });
});
```

### Agent Workspace Startup Process

1. Agent opens the workspace URL.
2. Workspace loads the CCP, AWS-managed apps, and all registered third-party apps.
3. Third-party services are initialized in the background (no visible UI).
4. Services receive lifecycle events and can interact with apps via AppController.

### Example: Contact Event Listener with App Launch

```typescript
import { AmazonConnectApp } from "@amazon-connect/core";
import { ContactClient } from "@amazon-connect/contact";
import { AppControllerClient } from "@amazon-connect/app-controller";

const app = await AmazonConnectApp.init({ instanceUrl });
const contactClient = new ContactClient(app);
const appController = new AppControllerClient(app);

contactClient.onIncoming(async (contact) => {
  const attrs = await contactClient.getAttributes(contact.contactId);
  if (attrs["customerTier"] === "premium") {
    await appController.launch({ appId: "premium-support-app" });
  }
});
```

### Example: Authentication Popup Pattern

```typescript
import { AmazonConnectApp } from "@amazon-connect/core";
import { AppControllerClient } from "@amazon-connect/app-controller";

const app = await AmazonConnectApp.init({ instanceUrl });
const appController = new AppControllerClient(app);

// Service that handles OAuth popup for an external CRM
await appController.launch({
  appId: "crm-auth-popup",
  launchMode: "popup",
  metadata: { returnUrl: window.location.href },
});
```

### Service Best Practices

- Create services sparingly — each one adds to workspace startup time.
- Use services for cross-cutting concerns (authentication, logging, routing logic).
- Do not duplicate functionality that an app already handles.
- Services persist for the entire agent session — clean up event listeners on destroy.

### Differences from 3P Apps

| Aspect | 3P App | 3P Service |
|---|---|---|
| UI | Visible tab in workspace | Hidden (no UI) |
| Lifecycle | Loaded when tab is active or on event | Loaded at workspace startup, runs entire session |
| Use case | Interactive features | Background automation |
| User interaction | Agent interacts directly | No direct interaction |

---

## C. Streams + AppManager Integration

For custom CCP embedding and advanced workspace integrations, use the `amazon-connect-streams` library alongside `@amazon-connect/app-manager`.

### amazon-connect-streams

The Streams library (`connect-streams.js`) enables embedding the CCP in a custom web page and programmatically controlling it.

```html
<script src="https://cdn.jsdelivr.net/npm/amazon-connect-streams/release/connect-streams.min.js"></script>
```

Or install via npm:

```bash
npm install amazon-connect-streams
```

### @amazon-connect/app-manager

The AppManager library manages AWS-managed applications within an embedded workspace.

```bash
npm install @amazon-connect/app-manager
```

### Architecture

```
Your Web Page
  |
  +-- connect.core.initCCP(containerDiv, config)
  |     |
  |     +-- Initializes CCP in containerDiv (iframe)
  |     +-- Sets up event handlers (contact, agent)
  |
  +-- AppManager plugin (optional)
        |
        +-- connect.appManager.launchApp(appConfig)
              |
              +-- Creates AppHost
                    |
                    +-- Renders app in iframe
```

### Basic CCP Embedding

```javascript
// Initialize CCP
connect.core.initCCP(document.getElementById("ccp-container"), {
  ccpUrl: "https://my-instance.my.connect.aws/ccp-v2/",
  loginPopup: true,
  loginPopupAutoClose: true,
  loginOptions: {
    autoClose: true,
    height: 600,
    width: 400,
  },
  softphone: {
    allowFramedSoftphone: true,
    disableRingtone: false,
  },
  region: "us-east-1",
});

// Agent events
connect.agent((agent) => {
  console.log("Agent connected:", agent.getName());

  agent.onStateChange((stateChange) => {
    console.log("Agent state:", stateChange.newState);
  });

  agent.onRoutingProfileChanged((routingProfile) => {
    console.log("Routing profile:", routingProfile.name);
  });
});

// Contact events
connect.contact((contact) => {
  console.log("New contact:", contact.getContactId());

  contact.onConnected(() => {
    console.log("Contact connected");
  });

  contact.onEnded(() => {
    console.log("Contact ended");
  });
});
```

### CCP with AppManager Plugin

```javascript
import "amazon-connect-streams";
import { AppManager } from "@amazon-connect/app-manager";

// Initialize CCP with AppManager plugin
connect.core.initCCP(document.getElementById("ccp-container"), {
  ccpUrl: "https://my-instance.my.connect.aws/ccp-v2/",
  loginPopup: true,
  softphone: { allowFramedSoftphone: true },
  region: "us-east-1",
});

// Initialize AppManager after CCP
const appManager = new AppManager({
  // Configuration for managed apps
});

// Launch a third-party app
appManager.launchApp({
  appId: "my-app-id",
  containerId: "app-container",  // DOM element to render into
});
```

### React Example with Dynamic App Management

```tsx
import React, { useEffect, useRef, useState } from "react";
import "amazon-connect-streams";
import { AppManager } from "@amazon-connect/app-manager";

interface ActiveApp {
  id: string;
  name: string;
  containerId: string;
}

export function ConnectWorkspace() {
  const ccpRef = useRef<HTMLDivElement>(null);
  const [activeApps, setActiveApps] = useState<ActiveApp[]>([]);
  const [appManager, setAppManager] = useState<AppManager | null>(null);

  useEffect(() => {
    if (!ccpRef.current) return;

    // Initialize CCP
    connect.core.initCCP(ccpRef.current, {
      ccpUrl: "https://my-instance.my.connect.aws/ccp-v2/",
      loginPopup: true,
      softphone: { allowFramedSoftphone: true },
      region: "us-east-1",
    });

    // Initialize AppManager
    const manager = new AppManager({});
    setAppManager(manager);

    // Listen for contact events to auto-launch apps
    connect.contact((contact) => {
      contact.onConnected(() => {
        const channelType = contact.getType();
        if (channelType === connect.ContactType.VOICE) {
          launchApp(manager, "voice-assist-app");
        }
      });
    });

    return () => {
      // Cleanup on unmount
      manager?.destroy();
    };
  }, []);

  function launchApp(manager: AppManager, appId: string) {
    const containerId = `app-${appId}-${Date.now()}`;
    manager.launchApp({
      appId,
      containerId,
    });
    setActiveApps((prev) => [
      ...prev,
      { id: appId, name: appId, containerId },
    ]);
  }

  function closeApp(app: ActiveApp) {
    appManager?.closeApp(app.id);
    setActiveApps((prev) => prev.filter((a) => a.containerId !== app.containerId));
  }

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* CCP Panel */}
      <div ref={ccpRef} style={{ width: 320, flexShrink: 0 }} />

      {/* App Panels */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {activeApps.map((app) => (
          <div key={app.containerId} style={{ flex: 1, position: "relative" }}>
            <button onClick={() => closeApp(app)}>Close {app.name}</button>
            <div id={app.containerId} style={{ width: "100%", height: "100%" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## D. SDK API Reference

Complete reference for all 10 SDK clients. Total: approximately 117 methods across all clients.

---

### Activity Client

**Package:** `@amazon-connect/core` (built-in)

Manages agent session activity and keep-alive.

| Method | Description |
|---|---|
| `onSessionExpiryWarning(callback)` | Fires when the agent session is approaching expiry. The callback receives the time remaining. Use this to prompt the agent to extend their session. |
| `offSessionExpiryWarning(callback)` | Unsubscribes from session expiry warning events. |
| `onSessionExpiryCleared(callback)` | Fires when the session expiry warning is cleared (agent extended session or the warning condition resolved). |
| `offSessionExpiryCleared(callback)` | Unsubscribes from session expiry cleared events. |
| `onExtensionError(callback)` | Fires when a session extension attempt fails. The callback receives the error details. |
| `offExtensionError(callback)` | Unsubscribes from extension error events. |
| `reportActive()` | Reports agent activity to extend the session. Call periodically to prevent session timeout. Returns a Promise that resolves when the report is acknowledged. |

```typescript
import { ActivityClient } from "@amazon-connect/core";

const activityClient = new ActivityClient(app);

activityClient.onSessionExpiryWarning((event) => {
  console.log(`Session expires in ${event.timeRemaining}ms`);
  // Prompt agent or auto-extend
  activityClient.reportActive();
});
```

---

### Agent Client

**Package:** `@amazon-connect/agent`

Manages agent state, routing profile, and channel configuration.

| Method | Signature | Description |
|---|---|---|
| `getARN()` | `() => Promise<string>` | Returns the agent's Amazon Resource Name (ARN). |
| `getName()` | `() => Promise<string>` | Returns the agent's display name. |
| `getState()` | `() => Promise<AgentState>` | Returns the current agent state (Available, Offline, custom status). |
| `getRoutingProfile()` | `() => Promise<RoutingProfile>` | Returns the agent's routing profile (queues, channels, concurrency). |
| `getChannelConcurrency()` | `() => Promise<ChannelConcurrency>` | Returns per-channel concurrency settings (e.g., voice: 1, chat: 5). |
| `getExtension()` | `() => Promise<string>` | Returns the agent's phone extension (for desk phone mode). |
| `listAvailabilityStates()` | `() => Promise<AvailabilityState[]>` | Lists all available agent states (built-in + custom statuses). |
| `listQuickConnects()` | `() => Promise<QuickConnect[]>` | Lists quick connects available to the agent. |
| `setAvailabilityState(stateARN)` | `(stateARN: string) => Promise<void>` | Sets the agent's state by ARN. |
| `setAvailabilityStateByName(name)` | `(name: string) => Promise<void>` | Sets the agent's state by display name (e.g., "Available", "Break"). |
| `setOffline()` | `() => Promise<void>` | Sets the agent to Offline state. |
| `onStateChanged(callback)` | `(cb: (event: StateChangedEvent) => void) => void` | Fires when the agent's state changes. Event includes old and new state. |
| `offStateChanged(callback)` | `(cb) => void` | Unsubscribes from state change events. |
| `onRoutingProfileChanged(callback)` | `(cb: (event: RoutingProfileEvent) => void) => void` | Fires when the agent's routing profile changes (admin reassignment). |
| `offRoutingProfileChanged(callback)` | `(cb) => void` | Unsubscribes from routing profile change events. |
| `onEnabledChannelListChanged(callback)` | `(cb: (event: ChannelListEvent) => void) => void` | Fires when the agent's enabled channel list changes. |
| `offEnabledChannelListChanged(callback)` | `(cb) => void` | Unsubscribes from channel list change events. |

```typescript
import { AgentClient } from "@amazon-connect/agent";

const agentClient = new AgentClient(app);

const state = await agentClient.getState();
console.log(`Agent is: ${state.name}`);

agentClient.onStateChanged((event) => {
  console.log(`State changed: ${event.previousState.name} -> ${event.newState.name}`);
});

// Set agent to available
await agentClient.setAvailabilityStateByName("Available");
```

---

### AppController Client

**Package:** `@amazon-connect/app-controller`

Controls third-party application lifecycle within the workspace.

| Method | Signature | Description |
|---|---|---|
| `close(appId)` | `(appId: string) => Promise<void>` | Closes a running third-party application. |
| `focus(appId)` | `(appId: string) => Promise<void>` | Brings a third-party application to the foreground. |
| `getApp(appId)` | `(appId: string) => Promise<AppInfo>` | Returns metadata about a specific registered application. |
| `getCatalog()` | `() => Promise<AppCatalog>` | Returns the full catalog of registered third-party applications. |
| `getConfig()` | `() => Promise<AppControllerConfig>` | Returns the AppController configuration. |
| `getActiveApps()` | `() => Promise<ActiveApp[]>` | Returns a list of currently active (running) applications. |
| `launch(config)` | `(config: LaunchConfig) => Promise<void>` | Launches a third-party application. Config includes appId and optional parameters (contactId, containerId). |

```typescript
import { AppControllerClient } from "@amazon-connect/app-controller";

const appController = new AppControllerClient(app);

// Get available apps
const catalog = await appController.getCatalog();
console.log("Available apps:", catalog.apps.map(a => a.name));

// Launch an app
await appController.launch({ appId: "my-crm-app" });

// Focus an app
await appController.focus("my-crm-app");

// Close an app
await appController.close("my-crm-app");
```

---

### Contact Client

**Package:** `@amazon-connect/contact`

Core contact handling -- accept, transfer, disconnect, and events for all channel types.

| Method | Signature | Description |
|---|---|---|
| `accept(contactId)` | `(contactId: string) => Promise<void>` | Accepts an incoming contact. |
| `addParticipant(config)` | `(config: AddParticipantConfig) => Promise<void>` | Adds a participant to a contact (conference/transfer). |
| `clear(contactId)` | `(contactId: string) => Promise<void>` | Clears a contact after ACW is complete. |
| `disconnectParticipant(config)` | `(config: DisconnectConfig) => Promise<void>` | Disconnects a specific participant from the contact. |
| `engagePreviewContact(contactId)` | `(contactId: string) => Promise<void>` | Engages a preview contact (outbound preview campaigns). |
| `getAttribute(contactId, key)` | `(contactId: string, key: string) => Promise<string>` | Gets a single contact attribute by key. |
| `getAttributes(contactId)` | `(contactId: string) => Promise<Record<string, string>>` | Gets all contact attributes. |
| `getChannelType(contactId)` | `(contactId: string) => Promise<ChannelType>` | Returns the contact's channel (VOICE, CHAT, EMAIL, TASK). |
| `getContact(contactId)` | `(contactId: string) => Promise<ContactDetails>` | Returns full contact details. |
| `getInitialContactId(contactId)` | `(contactId: string) => Promise<string>` | Returns the initial contact ID (for transferred contacts, this is the original). |
| `getParticipant(contactId, participantId)` | `(contactId: string, participantId: string) => Promise<Participant>` | Returns details about a specific participant. |
| `getParticipantState(contactId, participantId)` | `(contactId: string, participantId: string) => Promise<ParticipantState>` | Returns the state of a specific participant (connected, on hold, etc.). |
| `getPreviewConfiguration(contactId)` | `(contactId: string) => Promise<PreviewConfig>` | Returns preview configuration for outbound preview contacts. |
| `getQueue(contactId)` | `(contactId: string) => Promise<Queue>` | Returns the queue associated with the contact. |
| `getQueueTimestamp(contactId)` | `(contactId: string) => Promise<Date>` | Returns when the contact entered the queue. |
| `getStateDuration(contactId)` | `(contactId: string) => Promise<number>` | Returns how long the contact has been in its current state (ms). |
| `isPreviewMode(contactId)` | `(contactId: string) => Promise<boolean>` | Returns whether the contact is in preview mode. |
| `listContacts()` | `() => Promise<ContactSummary[]>` | Lists all active contacts for the agent. |
| `listParticipants(contactId)` | `(contactId: string) => Promise<Participant[]>` | Lists all participants in the contact. |
| `transfer(config)` | `(config: TransferConfig) => Promise<void>` | Transfers the contact to a queue, agent, or phone number. |
| `onConnected(callback)` | `(cb: (event) => void) => void` | Fires when a contact is connected. |
| `offConnected(callback)` | `(cb) => void` | Unsubscribes from connected events. |
| `onCleared(callback)` | `(cb: (event) => void) => void` | Fires when a contact is cleared (ACW complete). |
| `offCleared(callback)` | `(cb) => void` | Unsubscribes from cleared events. |
| `onMissed(callback)` | `(cb: (event) => void) => void` | Fires when a contact is missed (not accepted in time). |
| `offMissed(callback)` | `(cb) => void` | Unsubscribes from missed events. |
| `onIncoming(callback)` | `(cb: (event) => void) => void` | Fires when an inbound contact is presented to the agent. |
| `offIncoming(callback)` | `(cb) => void` | Unsubscribes from incoming events. |
| `onParticipantAdded(callback)` | `(cb: (event) => void) => void` | Fires when a participant is added to the contact. |
| `offParticipantAdded(callback)` | `(cb) => void` | Unsubscribes from participant added events. |
| `onParticipantDisconnected(callback)` | `(cb: (event) => void) => void` | Fires when a participant disconnects from the contact. |
| `offParticipantDisconnected(callback)` | `(cb) => void` | Unsubscribes from participant disconnected events. |
| `onParticipantStateChanged(callback)` | `(cb: (event) => void) => void` | Fires when a participant's state changes (e.g., placed on hold). |
| `onStartingAcw(callback)` | `(cb: (event) => void) => void` | Fires when the agent enters After Contact Work state for a contact. |
| `offStartingAcw(callback)` | `(cb) => void` | Unsubscribes from ACW events. |

```typescript
import { ContactClient } from "@amazon-connect/contact";

const contactClient = new ContactClient(app);

// Listen for incoming contacts
contactClient.onIncoming((event) => {
  console.log(`Incoming contact: ${event.contactId}, channel: ${event.channelType}`);
});

// Accept a contact
contactClient.onIncoming(async (event) => {
  await contactClient.accept(event.contactId);
});

// Get contact attributes
const attrs = await contactClient.getAttributes(contactId);
console.log("Customer tier:", attrs["CustomerTier"]);

// Transfer to a queue
await contactClient.transfer({
  contactId,
  queueARN: "arn:aws:connect:us-east-1:123456789:instance/abc/queue/xyz",
});

// Listen for ACW
contactClient.onStartingAcw((event) => {
  console.log(`Contact ${event.contactId} entering ACW`);
});
```

---

### Email Client

**Package:** `@amazon-connect/email`

Handles email-specific operations (drafts, metadata, threading).

| Method | Signature | Description |
|---|---|---|
| `createDraft(config)` | `(config: DraftConfig) => Promise<DraftInfo>` | Creates a new email draft for a contact. Config includes subject, body (HTML), recipients, attachments. |
| `getMetadata(contactId)` | `(contactId: string) => Promise<EmailMetadata>` | Returns email metadata (subject, from, to, cc, bcc, timestamp, headers). |
| `getTree(contactId)` | `(contactId: string) => Promise<EmailThread>` | Returns the full email thread tree (original + all replies/forwards). |
| `sendDraft(draftId)` | `(draftId: string) => Promise<void>` | Sends a previously created draft. |
| `onAccepted(callback)` | `(cb: (event) => void) => void` | Fires when an email contact is accepted by the agent. |
| `offAccepted(callback)` | `(cb) => void` | Unsubscribes from email accepted events. |
| `onDraftCreated(callback)` | `(cb: (event) => void) => void` | Fires when a draft is created. |
| `offDraftCreated(callback)` | `(cb) => void` | Unsubscribes from draft created events. |

```typescript
import { EmailClient } from "@amazon-connect/email";

const emailClient = new EmailClient(app);

// Get email thread
const thread = await emailClient.getTree(contactId);
console.log("Thread messages:", thread.messages.length);

// Create and send a reply
const draft = await emailClient.createDraft({
  contactId,
  subject: "Re: Your inquiry",
  body: "<p>Thank you for contacting us...</p>",
  recipients: { to: ["customer@example.com"] },
});
await emailClient.sendDraft(draft.draftId);
```

---

### File Client

**Package:** `@amazon-connect/file`

Manages file uploads and downloads for attachments across channels.

| Method | Signature | Description |
|---|---|---|
| `batchGetMetadata(fileIds)` | `(fileIds: string[]) => Promise<FileMetadata[]>` | Returns metadata for multiple files (name, size, type, upload status). |
| `completeUpload(uploadId)` | `(uploadId: string) => Promise<void>` | Completes a multipart upload that was started with `startUpload`. |
| `delete(fileId)` | `(fileId: string) => Promise<void>` | Deletes a file. |
| `download(fileId)` | `(fileId: string) => Promise<Blob>` | Downloads a file. Returns the file content as a Blob. |
| `startUpload(config)` | `(config: UploadConfig) => Promise<UploadInfo>` | Initiates a file upload. Config includes file name, size, content type, and the associated contact ID. Returns upload URL and upload ID. |

```typescript
import { FileClient } from "@amazon-connect/file";

const fileClient = new FileClient(app);

// Upload a file
const upload = await fileClient.startUpload({
  contactId,
  fileName: "report.pdf",
  fileSizeInBytes: file.size,
  contentType: "application/pdf",
});

// Upload file content to the presigned URL
await fetch(upload.uploadUrl, {
  method: "PUT",
  body: file,
  headers: { "Content-Type": "application/pdf" },
});

// Complete the upload
await fileClient.completeUpload(upload.uploadId);

// Download a file
const blob = await fileClient.download(fileId);
```

---

### MessageTemplate Client

**Package:** `@amazon-connect/message-template`

Manages message templates for email and chat responses.

| Method | Signature | Description |
|---|---|---|
| `getContent(templateId)` | `(templateId: string) => Promise<TemplateContent>` | Returns the full content of a message template (subject, body, placeholders). |
| `isEnabled()` | `() => Promise<boolean>` | Returns whether message templates are enabled for the instance. |
| `search(query)` | `(query: SearchQuery) => Promise<TemplateSearchResult>` | Searches message templates by keyword, category, or channel type. |

```typescript
import { MessageTemplateClient } from "@amazon-connect/message-template";

const templateClient = new MessageTemplateClient(app);

// Check if templates are enabled
const enabled = await templateClient.isEnabled();

// Search for templates
const results = await templateClient.search({
  query: "password reset",
  channelType: "EMAIL",
});

// Get template content
const template = await templateClient.getContent(results.templates[0].id);
console.log("Template body:", template.body);
```

---

### QuickResponses Client

**Package:** `@amazon-connect/quick-responses`

Manages quick responses (canned messages with shortcuts).

| Method | Signature | Description |
|---|---|---|
| `isEnabled()` | `() => Promise<boolean>` | Returns whether quick responses are enabled for the instance. |
| `search(query)` | `(query: SearchQuery) => Promise<QuickResponseSearchResult>` | Searches quick responses by keyword, shortcut, or category. Returns matching responses with their content and shortcuts. |

```typescript
import { QuickResponsesClient } from "@amazon-connect/quick-responses";

const qrClient = new QuickResponsesClient(app);

// Search for quick responses
const results = await qrClient.search({ query: "greeting" });
results.responses.forEach((qr) => {
  console.log(`Shortcut: ${qr.shortcut}, Content: ${qr.content}`);
});
```

---

### User Client

**Package:** `@amazon-connect/core` (built-in)

Manages user preferences and language settings.

| Method | Signature | Description |
|---|---|---|
| `getLanguage()` | `() => Promise<string>` | Returns the agent's language preference (e.g., "en-US", "es-ES"). |
| `onLanguageChanged(callback)` | `(cb: (event: LanguageEvent) => void) => void` | Fires when the agent changes their language preference. |
| `offLanguageChanged(callback)` | `(cb) => void` | Unsubscribes from language change events. |

```typescript
const language = await app.getUser().getLanguage();
console.log("Agent language:", language);

app.getUser().onLanguageChanged((event) => {
  console.log("Language changed to:", event.language);
  // Update app localization
});
```

---

### Voice Client

**Package:** `@amazon-connect/voice`

Controls voice-specific operations (hold, resume, conference, outbound, DTMF, voice enhancement).

| Method | Signature | Description |
|---|---|---|
| `hold(contactId)` | `(contactId: string) => Promise<void>` | Places the customer on hold. |
| `resume(contactId)` | `(contactId: string) => Promise<void>` | Resumes the customer from hold. |
| `conference(contactId)` | `(contactId: string) => Promise<void>` | Merges all participants into a conference call. |
| `createOutbound(config)` | `(config: OutboundConfig) => Promise<OutboundResult>` | Initiates an outbound call. Config includes destination number, outbound caller ID, and optional contact flow. |
| `getCustomerNumber(contactId)` | `(contactId: string) => Promise<string>` | Returns the customer's phone number. |
| `getOutboundPermission()` | `() => Promise<OutboundPermission>` | Returns whether the agent has outbound calling permission and allowed countries. |
| `isOnHold(contactId)` | `(contactId: string) => Promise<boolean>` | Returns whether the customer is currently on hold. |
| `listDialableCountries()` | `() => Promise<Country[]>` | Lists countries the agent is allowed to dial. |
| `getVoiceEnhancementMode(contactId)` | `(contactId: string) => Promise<VoiceEnhancementMode>` | Returns the current voice enhancement mode (noise cancellation, etc.). |
| `setVoiceEnhancementMode(contactId, mode)` | `(contactId: string, mode: VoiceEnhancementMode) => Promise<void>` | Sets the voice enhancement mode for a contact. |
| `canResumeParticipant(contactId, participantId)` | `(contactId: string, participantId: string) => Promise<boolean>` | Returns whether a specific held participant can be resumed. |
| `canResumeSelf(contactId)` | `(contactId: string) => Promise<boolean>` | Returns whether the agent can resume themselves from hold. |
| `getVoiceEnhancementModelPaths()` | `() => Promise<string[]>` | Returns available voice enhancement model paths. |
| `onHold(callback)` | `(cb: (event) => void) => void` | Fires when a participant is placed on hold. |
| `offHold(callback)` | `(cb) => void` | Unsubscribes from hold events. |
| `onResume(callback)` | `(cb: (event) => void) => void` | Fires when a participant is resumed from hold. |
| `offResume(callback)` | `(cb) => void` | Unsubscribes from resume events. |
| `onConference(callback)` | `(cb: (event) => void) => void` | Fires when a conference is established. |
| `offConference(callback)` | `(cb) => void` | Unsubscribes from conference events. |
| `onCapabilityChanged(callback)` | `(cb: (event) => void) => void` | Fires when voice capabilities change (e.g., hold/resume availability). |
| `offCapabilityChanged(callback)` | `(cb) => void` | Unsubscribes from capability change events. |
| `onVoiceEnhancementChanged(callback)` | `(cb: (event) => void) => void` | Fires when voice enhancement mode changes. |
| `offVoiceEnhancementChanged(callback)` | `(cb) => void` | Unsubscribes from voice enhancement change events. |
| `onOutboundConnected(callback)` | `(cb: (event) => void) => void` | Fires when an outbound call connects. |
| `offOutboundConnected(callback)` | `(cb) => void` | Unsubscribes from outbound connected events. |
| `onOutboundFailed(callback)` | `(cb: (event) => void) => void` | Fires when an outbound call fails. |
| `offOutboundFailed(callback)` | `(cb) => void` | Unsubscribes from outbound failed events. |

```typescript
import { VoiceClient } from "@amazon-connect/voice";

const voiceClient = new VoiceClient(app);

// Hold and resume
await voiceClient.hold(contactId);
console.log("Customer on hold:", await voiceClient.isOnHold(contactId));
await voiceClient.resume(contactId);

// Make outbound call
const result = await voiceClient.createOutbound({
  destinationNumber: "+15551234567",
  outboundCallerId: "+15559876543",
});

// Voice enhancement
const mode = await voiceClient.getVoiceEnhancementMode(contactId);
await voiceClient.setVoiceEnhancementMode(contactId, "NOISE_CANCELLATION");

// Events
voiceClient.onHold((event) => {
  console.log(`Participant ${event.participantId} placed on hold`);
});

voiceClient.onResume((event) => {
  console.log(`Participant ${event.participantId} resumed`);
});
```
