# Saytm UI/UX Design Specification

This document records the interaction model, visual system, responsive behavior, accessibility decisions, and settled design requirements of the Saytm demo. It is written as a portable design brief: it can guide a visually similar conversational-finance interface without copying the implementation or its demo data.

## 1. Product and experience goals

Saytm is a voice-first, bilingual financial-assistance prototype. The interface should feel calm, trustworthy, legible, and human-supported—not like a generic mobile chat mockup stretched across a desktop. It supports Hindi and Indian English, with text always available when speech is unavailable.

Design priorities, in order:

1. **Orient before asking.** Open on a short welcome, not an already-open customer account or an empty agent workspace.
2. **Make customer selection deliberate.** Do not inspect or display a customer's profile data until the visitor chooses a demo account.
3. **Keep the conversation primary.** Financial decisions, consent, explanations, waiting states, and human replies all belong in the same customer conversation.
4. **Make high-stakes information understandable.** Use plain language, visible consent, separated facts and actions, and explicit human escalation.
5. **Keep speech controllable.** A user should know when speech is playing and be able to stop it without losing their place.
6. **Support real screen sizes.** Customer and staff surfaces should each work as a designed desktop layout and a designed phone layout.
7. **Reduce visual load without hiding meaning.** Zen mode changes density, hierarchy, and motion—not just the hue.

The interface is a prototype. Its profiles, calculations, statements, signatures, and integrations are simulated and must not be presented as live financial services.

## 2. Information architecture

There are two distinct but connected surfaces:

- **Customer app (`/`)** — welcome, language choice, account switching, conversation, consent and product information, voice controls, and a waiting state for human support.
- **Staff inbox (`/admin`)** — staff sign-in, a live conversation queue, transcript review, takeover/intervention, and human replies.

Opening the staff inbox does not replace or redirect the customer's page. A customer support link opens the staff surface in a new tab; the customer remains in the original conversation.

## 3. Customer app: first visit and account switching

### 3.1 Welcome-first state

- Start with a brief welcome and a clear statement about what the assistant helps with.
- Do not select a customer automatically, create a customer session, or reveal customer-specific data on initial load.
- The default voice agent reads only the short welcome line. It should not narrate all supporting copy, disclaimers, profile choices, or page chrome.
- Include a visible, conventional volume/speaker-shaped button beside the welcome text. It reads the welcome when selected and changes to a stop state while speaking.
- Offer language selection near the top of the page. A language change updates visible copy and speaks the welcome in the newly selected locale.
- A theme change also reads the short welcome in the currently selected language, as requested for this product experience.

### 3.2 Profile control

The profile menu is the account-switching control; there is no separate “Continue” action.

- **Phone:** Use a compact profile/avatar button in the header's right-side control group.
- **Desktop:** Put the profile card at the bottom-left of the welcome sidebar. Keep the descriptive footer text above the profile card and align both to a shared left edge. Give the profile card enough width for its two-line label; do not let the label wrap into an awkward narrow pill.
- The menu contains the available demo customer profiles, the active profile state, consent revocation when applicable, and staff sign-in.
- Put staff sign-in inside this profile menu and open it in a new tab.
- Selecting an account starts that account's conversation immediately. Update the profile label, greeting, conversation header, and session content together.
- Close the profile menu after selection. Never show one account's old transcript while loading another account.

## 4. Customer app: desktop and phone layouts

### 4.1 Desktop composition

Use a bounded, centered application frame with a two-column workspace:

- A narrow, persistent **welcome/sidebar column** contains the welcome heading, concise supporting text, optional short welcome audio control, a privacy/consent note, and the profile card anchored to the bottom.
- A wider **conversation column** contains the current conversation title/status, centered empty state when no account is selected, and the chat/input stack after selection.
- Keep the chat column flexible and substantially wider than the sidebar. Set a maximum application width so very wide monitors do not create uncomfortably long lines.
- The header spans the application frame. Arrange language, theme, Zen, and profile controls in a stable, right-aligned action group.
- The sidebar's bottom content must not collide with its profile control at shorter viewport heights; allow the sidebar to scroll or adapt spacing rather than overlap.

### 4.2 Phone composition

At phone widths, reflow instead of shrinking the desktop columns:

- The header becomes compact and wraps its action controls cleanly.
- Keep the Zen label complete and visible. Keep language, theme, Zen, and profile controls distinct, with enough hit area and no horizontal page overflow.
- Place the profile avatar at the upper-right within the header action group.
- Stack the welcome content above the conversation. Reduce decorative copy before reducing message legibility.
- Make the chat area tall enough to read and operate; keep the input controls reachable near the bottom of the viewport.
- Respect safe-area insets for bottom input controls.
- Keep quick-query chips horizontally scrollable rather than squeezing them into tiny buttons.
- Chat bubbles can use nearly the full content width on a phone, with consistent insets and no clipping of the speaker control.

### 4.3 Empty and active states

- **No account selected:** Show a centered, reassuring “ready when you are” state in the conversation area. Explain that choosing a profile begins the conversation; do not show a dead-end continue button.
- **Account selected:** Show a concise identity/context line, then a scrollable transcript. Keep the composer and relevant quick queries grouped at the bottom of the chat column.
- **Loading or request failure:** Preserve clear error feedback. Do not silently display a success-shaped empty conversation.
- **Waiting for a human:** Keep the transcript and page in place. Show a waiting message/status; never send the customer to the staff surface.
- **Human connected:** Replace waiting copy with joined/connected status and identify human-authored replies distinctly.

## 5. Conversation and message design

### 5.1 Customer-side alignment

On the customer page:

- **Customer-authored messages:** align to the right.
- **Assistant replies:** align to the left.
- **Human-agent replies:** align to the left, with a restrained but distinct human-support accent and a visible author label.
- Use a readable line height, comfortable bubble padding, bounded message width, and text wrapping that handles long words and links.
- Do not rely on alignment or color alone to identify the speaker. Keep sender labels available where helpful.
- Financial cards (consent, offer/KFS, policy clause, comparison, receipt, handoff) should span the message column rather than imitate small chat bubbles.

### 5.2 Message audio

- Every message that can be read aloud has an adjacent speaker button with a conventional volume/speaker glyph.
- Use a consistent button shape across the welcome control, customer messages, and staff transcript. Avoid irregular or decorative speaker shapes.
- Pressing a message's speaker button starts that message. Pressing the **same button again while it is speaking stops it**. Starting another message stops the previous utterance so speech never overlaps.
- The active button changes to a recognizable stop/pause indicator and exposes an accessible “Stop reading aloud” name.
- Store the message locale on the message and use that locale for speech playback.
- Assistant replies may auto-speak according to the customer's read-aloud preference.
- Human-authored text must **not** auto-speak. It remains available through its own speaker button.
- The human-takeover notice is an explicit exception: read the notice when it arrives so the customer hears that the AI has paused and a person has taken over. Use the current language; localize the notice for Hindi customers.

### 5.3 Conversation actions and cards

- **Quick query:** Label preset prompts “Quick query” (not “Quick voice”). Use short, horizontally scrollable examples for common loan, insurance, and human-support intents.
- **Consent:** State what data is requested and why before the choice. Use a clear primary grant action and a visually secondary decline action. Make revocation discoverable in the profile menu and require confirmation before resetting a session.
- **Audit visibility:** Keep the raw operational audit log out of the customer-facing controls; retain server-side event recording for the demo. Customers need clear consent and conversation status, not backend event tooling.
- **Loan offer/KFS:** Separate the amount, tenure, EMI, rate, fees/tax, net proceeds, repayment total, and source/basis into a scannable grid. Tenure repricing controls sit beside the offer they affect.
- **Insurance clause:** Identify plan and clause, show the retrieved wording and plain-language context, and visually distinguish the citation from chat.
- **Comparison:** Use a semantic, responsive comparison table; preserve row labels and avoid forcing a wide table beyond the viewport.
- **Receipt:** Make its reference and amount readable and distinct. Do not imply a real approval when the operation is simulated.
- **KYC/agent request:** Explain that the request is waiting for a human. Preserve the active chat and update status when the agent joins.

## 6. Voice, language, and pronunciation

- Use browser-native speech recognition and synthesis where available; always leave the text entry path visible.
- The microphone is a professional, familiar button with a simple microphone SVG—not a playful emoji. Show a clear listening/recording state and an actionable permission or service error.
- Support Hindi (`hi-IN`) and Indian English (`en-IN`) on both interface and speech. Do not keep Hindi voice playback after the customer switches to English, or vice versa.
- Read the short welcome on initial app load. Selecting a profile speaks the personalized greeting. Switching language or theme speaks the short welcome in the selected/current language.
- Pronounce the brand as the phrase **“Say T M”**: “Say” is the English verb for speaking, followed by the letters T and M. In browser speech text, expand the written brand `Saytm` to a pronunciation-friendly form such as `Say, T. M`; do not say it as “say-tum” or “say-tee-em”.
- Keep the spoken copy short, especially at first load. Avoid reading full layout text or financial cards automatically.
- Respect the explicit read-aloud preference for assistant replies. Manual message playback remains available even when automatic narration is muted.
- On the staff/customer transcript, include a per-message playback control. Human replies are always manual playback only.

## 7. Light, dark, and Zen themes

### 7.1 Persistent light/dark theme

- Both customer and staff surfaces provide a visible theme toggle.
- Persist the preference across reloads using a shared key (`saytm-theme`) so switching between customer and staff pages keeps the chosen theme.
- Make the toggle unmistakable in light mode: use a high-contrast icon, visible border, solid light surface, generous hit area (approximately 40 × 40 CSS px), hover/focus state, and an accessible name that says which theme will be activated.
- Do not use a pale gray icon on white without a contrasting edge.

### 7.2 Standard light palette

The standard light presentation is restrained and neutral:

- Main surfaces: white and very light cool gray, with subtle gradients rather than saturated fills.
- Text: charcoal/near-black for primary copy; mid-gray only for secondary metadata and only when contrast remains readable.
- Primary buttons: graphite/charcoal gradients with white text.
- Customer outgoing bubble: dark neutral/charcoal with white text.
- Incoming assistant bubbles: white/light-gray surface with a quiet border.
- Human agent replies: a muted green/teal cue distinct from both assistant and customer, not a fully new color system.

### 7.3 Standard dark palette

The standard dark theme should feel refined, not electric blue:

- Use deep charcoal/navy surfaces with softly differentiated panels and borders.
- Use muted teal/cyan for action emphasis and the customer's outgoing bubble; avoid a large area of saturated royal blue.
- Keep assistant messages neutral and human replies muted green.
- Ensure input text, placeholders, secondary metadata, message labels, icons, and controls remain legible on their own backgrounds.

### 7.4 Zen mode

Zen is a **layout and attention mode**, not just a color toggle:

- Retain the same customer conversation and account; never create a separate session.
- Reduce competing UI: hide nonessential quick queries and promotional/guide elements, simplify the conversation header, widen the usable conversation area, and soften card decoration.
- Use quieter spacing, fewer borders, softer surfaces, and a very subtle ambient background glow. Avoid strong animation; respect reduced-motion preferences.
- Keep essential functions—language, account access, theme, message playback, and text/voice input—available.
- Slow narration modestly (the current design uses roughly `0.88×` in Zen versus `0.95×` standard).
- The Zen control remains anchored in the same header action group before and after toggling. The label is always the full text **“Zen mode”**; do not move, resize, or replace it with an emoji-only label.
- Persist Zen separately from light/dark theme. The theme must remain independently switchable while Zen is active.

### 7.5 Contrast rules

The earlier implementation exposed low-contrast text in Zen in both light and dark palettes. For every final theme:

- Recheck headings, paragraphs, metadata, card text, table labels, profile labels, empty states, buttons, focus rings, and icons—not only body text.
- Use a consistent near-black forest text on pale sage surfaces in Zen light mode.
- Use warm near-white text on dark forest surfaces in Zen dark mode, with brighter secondary text than the standard theme's decorative metadata.
- Set explicit theme rules for icons and welcome illustrations; do not let a light-mode icon inherit an unrelated dark-theme text color.
- Aim for at least 4.5:1 contrast for normal-size text and 3:1 for large text and important UI boundaries, using a contrast checker during implementation.

## 8. Staff inbox

### 8.1 Structure

- **Desktop:** Fixed-width conversation queue on the left; selected transcript and actions on the right.
- **Phone:** Queue becomes a compact, horizontally browsable or vertically limited list above the selected conversation; transcript and composer use the remaining height.
- Give each queue item a customer name, short session metadata, and a clear state: AI active, waiting, or connected.
- Prioritize waiting handoffs, but allow staff to monitor active AI conversations.
- Keep the theme control visible in the top bar and share the customer's persisted theme preference.

### 8.2 Transcript color and alignment

The staff view's left/right semantics are from the **staff operator's** perspective:

- **Customer messages:** left aligned; use a soft blue-tinted surface and readable dark text in light mode.
- **AI assistant messages:** left aligned; use a neutral gray surface so assistant text is distinct from customer text.
- **Human staff messages:** right aligned; use a quiet green-tinted surface and a visible staff author label.
- In dark mode, preserve the same role distinctions with dark blue, charcoal, and dark green surfaces and high-contrast text.
- Keep sender labels and timestamps secondary but legible. Color reinforces the role; it does not replace the label.
- Give every transcript message its own speaker button. Playback is on demand; do not auto-read any staff-authored text.

### 8.3 Takeover and reply gating

- In an AI-active conversation, show an **Intervene in AI chat** action and a concise explanation that the assistant is currently handling the conversation.
- Keep the reply composer hidden until either the customer has requested a human and staff chooses **Join conversation**, or staff explicitly intervenes.
- Joining or intervening pauses further AI replies and reveals the composer.
- Intervention adds a clear takeover notice to the transcript. The customer-side app reads that notice aloud once as a system/human-support announcement.
- After takeover, customer messages appear to staff without triggering AI answers; staff replies appear in the existing customer conversation.
- Keep errors in the selected conversation panel. Do not report a successful takeover until the server confirms it.

## 9. Accessibility and interaction details

- Use semantic buttons, forms, headings, status regions, and labels. Do not rely on an icon without an accessible name.
- Add visible keyboard focus. The Zen shortcut is `Alt+Z`; do not intercept it while Control/Command/Meta is held.
- Provide large, separated touch targets for microphone, send, language, theme, Zen, and profile controls.
- Use button state (`aria-pressed`) for toggles and speaker playback. Keep accessible names synchronized with current state.
- Announce handoff/waiting/connected status through a status region. Keep transcript updates understandable to assistive technology.
- Honor `prefers-reduced-motion`; the Zen breathing glow should be subtle and nonessential.
- Do not put critical financial disclosures only into speech, color, animation, or tooltips.
- Retain typed interaction on browsers that do not support speech recognition.

## 10. Visual system and reusable tokens

Use semantic tokens rather than scattering literals:

| Token | Purpose | Guidance |
|---|---|---|
| `--surface` | Main panels and cards | White/light gray in light mode; charcoal/forest in dark mode |
| `--surface-muted` | Inputs, assistant bubbles, quiet controls | Slightly distinct from the main surface |
| `--text-primary` | Main copy and titles | Near-black in light mode; near-white in dark mode |
| `--text-secondary` | Descriptions, timestamps, metadata | Readable gray/green-gray, never faint by default |
| `--border` | Separators and control outlines | Visible without looking heavy |
| `--accent-primary` | Main action and selected state | Graphite in neutral light mode; restrained teal in dark mode |
| `--accent-human` | Human-agent messages | Muted green/teal, consistently applied |
| `--accent-customer` | Staff-side customer messages | Soft blue tint, clearly distinct from assistant neutral |
| `--focus` | Keyboard outline | High contrast in every theme |

Use a compact spacing scale (roughly 4, 8, 12, 16, 24, 32, 48 px), consistent radii (small controls around 8–12 px; cards and conversation surfaces around 14–22 px), and subtle elevation. Prefer font sizes that remain comfortable at 100% zoom; do not make metadata so small that it carries essential meaning.

Typography should support Devanagari shaping and English text with compatible line height. The current demo uses Hind for Hindi/UI copy and Fraunces for brand/display moments; a similar project may substitute licensed, locally available fonts while preserving Hindi readability and language-appropriate fallbacks.

## 11. Settled product-specific design decisions

These are intentional requirements from the design iteration and should be treated as approved baseline behavior:

1. The default screen is a general welcome, not a customer conversation; account selection is explicit.
2. Selecting a different customer starts the chat immediately. There is no Continue button.
3. Mobile profile access is in the top-right header. Desktop profile access is at the bottom-left of the sidebar, with its supporting text aligned above it.
4. The default voice reads only the short welcome. Personalized greetings are spoken when a customer's chat starts.
5. The spoken brand is “Say T M,” not “say-tum” or “say-tee-em.”
6. Staff sign-in lives inside the profile menu and opens a separate tab.
7. KYC/human-support requests leave the customer on a waiting screen in the same chat while staff uses a separate inbox.
8. Zen mode must materially reduce distraction and retain a fixed position, a full “Zen mode” label, and readable light/dark colors.
9. Message speaker buttons must start and stop that message. Human-agent text never auto-speaks; the takeover notice does.
10. Both customer and staff apps have persistent light/dark controls. Standard light mode is neutral white/gray with charcoal actions; dark mode uses refined charcoal with a restrained teal accent.
11. Staff transcript colors distinguish customer, assistant, and human replies without abandoning the shared neutral palette.
12. The interface must be purpose-designed for desktop and phone rather than a phone-only layout enlarged to desktop.
13. Keep consent revocation available with confirmation, but do not expose the raw audit log as a customer-facing button.

## 12. Design QA checklist

Before accepting a related interface, check:

- [ ] First load has no active customer and does not display customer-specific information.
- [ ] Only the short welcome is spoken initially; the spoken locale follows the selected language.
- [ ] Profile selection immediately opens the selected customer's conversation.
- [ ] Theme and Zen buttons remain at stable coordinates across their toggles.
- [ ] The light-mode theme button has a clearly visible icon, border, focus ring, and state label.
- [ ] Every text-bearing surface is readable in standard light, standard dark, Zen light, and Zen dark.
- [ ] The desktop sidebar footer/profile aligns as a single column; the phone profile icon stays in the header.
- [ ] There is no horizontal overflow at common phone widths; controls remain reachable.
- [ ] Chat sides match the correct perspective on both customer and staff screens.
- [ ] A message speaker button can stop its current utterance and starting another message cancels the previous one.
- [ ] Human-agent messages do not auto-speak; the takeover announcement does.
- [ ] Staff cannot type before joining/intervening; a confirmed takeover pauses AI responses.
- [ ] Waiting for a human does not navigate away from the customer chat.
- [ ] Reduced-motion preferences and keyboard focus are respected.
- [ ] Mock behavior and the non-production status are stated clearly.

## 13. Implementation references

The current customer UI and its inline styles/behavior are in [`frontend/index.html`](./frontend/index.html). The staff inbox is in [`frontend/admin.html`](./frontend/admin.html). The handoff/session API is in [`backend/app.py`](./backend/app.py). Product journey details are in [`docs/WORKFLOW.md`](./docs/WORKFLOW.md); the project boundaries and feature status are in [`README.md`](./README.md) and [`docs/FEATURE_STATUS.md`](./docs/FEATURE_STATUS.md).
