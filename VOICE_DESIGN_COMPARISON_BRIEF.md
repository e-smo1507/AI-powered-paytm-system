# Saytm Voice, Design, and Feature Comparison Brief

Use this document as a portable specification when reviewing another demo of the same product. It records the customer-approved requests and the intended final behavior in this Saytm implementation. Compare both demos against the same criteria; do not assume that visual similarity alone means the journeys work.

The app is a prototype using mock customer/partner data, local deterministic rules and retrieval, and browser speech. It does not need an external AI-service API key to run. No production financial, legal, privacy, or accessibility certification is implied.

## 1. Product experience in one paragraph

Saytm is a bilingual Hindi/Indian-English voice-and-text banking-assistance demo for loan and health-insurance questions. It opens on a general welcome, lets the visitor explicitly choose a demo customer, and starts that customer's chat immediately. Speech should be brief, correctly localized, controllable, and never a substitute for readable on-screen content. The customer stays in their chat while a separate staff inbox handles human support. The visual design has distinct responsive phone and desktop layouts, persistent light/dark themes, and a genuinely less distracting Zen mode.

## 2. Voice behavior: required

### First visit and customer greeting

- On a fresh visit, do not automatically select a profile, create a customer session, or reveal customer data.
- The default voice reads **only one short welcome line**. It must not read all the explanatory page copy.
- The welcome has an adjacent, recognizable volume/speaker-shaped button with an accessible label. It changes to a stop state while speaking.
- Choosing a customer starts that customer's chat immediately and speaks the personalized greeting. Do not add a separate Continue button.
- Changing the interface language speaks the welcome in the newly selected language.
- Changing the light/dark theme also speaks the welcome in the currently selected language.

### Language and pronunciation

- Support Hindi (`hi-IN`) and Indian English (`en-IN`) for visible copy and speech wherever the browser has a suitable voice.
- A voice utterance must use the active message's language, not a stale page or browser default.
- Pronounce the brand as **“Say T M”**: “Say” is the English word meaning speak, followed by the letters T and M. It must not sound like “say-tum” or “say-tee-em.”
- In Hindi speech, pronounce **AI** as the Hindi letter names **“एआई”**, not the sound “अइ.” Keep the on-screen spelling “AI” if desired; normalize the spoken text.
- Apply pronunciation fixes consistently to the welcome, personalized greetings, assistant replies, takeover announcements, and manually played transcript messages wherever the brand/acronym appears.

### Message speech and interruption

- Each readable chat/transcript message has its own nearby conventional speaker/volume button. Use one consistent button silhouette; avoid oddly shaped icons.
- Clicking a message's speaker starts that exact message. Clicking the **same button during playback stops it** and returns it to its idle state.
- Starting playback on another message cancels the previous utterance; never speak two messages over each other.
- Expose playback state using a visible stop/pause glyph, `aria-pressed`, and a localized accessible name such as “Stop reading aloud.”
- The read-aloud preference controls automatic assistant speech. Manual playback remains available when automatic speech is muted.
- Human-authored agent messages **never auto-speak**. The customer or staff member may play/stop an individual human message manually.
- The intervention/takeover notice is a special system announcement: display it in the customer's selected language and speak it once in that language.
- In Hindi takeover speech, say “एआई सहायक” for AI; do not say “अइ सहायक.”

### Microphone and text fallback

- Use browser speech recognition when supported and permission is granted; typed input remains available at all times.
- Use a familiar professional microphone icon (not a childish emoji) with a clear listening/recording state.
- Microphone errors should explain the cause and next step, including unsupported browser, denied permission, missing microphone, network error, or no speech.
- Preset prompts are called **Quick query**, not “Quick voice.” They remain optional shortcuts, not the only way to interact.
- Respect the customer's explicit language selection for recognition and speech output.

## 3. Customer journey and account controls

- Start on a welcome/empty state, not inside a customer chat.
- The customer profile/account picker is the single place to switch demo identity:
  - **Phone:** profile/avatar control in the top-right header.
  - **Desktop:** profile card at the bottom-left of the welcome sidebar.
- On desktop, align the profile card and its explanatory/footer text to the same left edge. Keep enough card width for both lines of the profile label; do not let the label wrap into a narrow or misaligned control.
- Selecting an account immediately opens that account's chat. Close the menu and update the transcript, profile label, greeting, and conversation heading together.
- Keep staff sign-in inside the profile menu. Open the staff inbox in a new tab so the customer conversation stays intact.
- A customer-requested human/KYC interaction displays a waiting-for-agent state in the **current chat**. Do not navigate to the staff site or make the customer wait on a new screen.
- The customer can revoke data consent with clear confirmation. Keep raw audit-log tooling out of customer controls; event recording is a backend/demo operation.

## 4. Message layout and human handoff

### Customer screen alignment

- Customer's own messages: **right**.
- Assistant replies: **left**.
- Human-agent replies: **left**, labeled as human support and distinguished with a restrained human-support color.
- Financial/consent/policy cards use a structured card layout, not tiny speech bubbles.
- Every role remains identifiable by author text/metadata as well as color and alignment.

### Staff screen alignment and role colors

Alignment is from the staff operator's point of view:

- Customer messages: **left**, soft blue-tinted surface.
- AI assistant messages: **left**, neutral gray surface.
- Staff messages: **right**, restrained green-tinted surface.
- Preserve the same role distinctions in dark mode with readable blue, charcoal, and green surface variations. Do not replace the overall palette with unrelated saturated colors.
- Keep author names/timestamps legible but secondary. Each message has manual speaker/stop playback.

### Staff takeover behavior

- `/admin` is a separate, authenticated staff inbox with a queue of waiting handoffs and active AI chats.
- Staff may monitor an AI conversation, but the reply composer stays hidden until:
  1. the customer requested human support and staff selects **Join conversation**, or
  2. staff chooses **Intervene in AI chat**.
- On confirmed intervention/join, pause AI responses, show the human composer, and add a takeover notice to the transcript.
- The takeover notice's **visible text and speech use the customer's selected language**. For Hindi, the user-facing message must not remain English while only the TTS is Hindi.
- Subsequent customer messages remain in the transcript for the human and do not trigger another AI reply.
- Do not auto-speak ordinary human replies. The takeover notice is the intentional spoken exception.

## 5. Visual design requirements

### Shared composition

- The interface should feel calm, credible, and usable for a sensitive financial conversation—not like a phone-only prototype enlarged for desktop.
- Use a bounded desktop application frame and a two-column workspace: narrower welcome/profile sidebar and wider conversation area.
- At phone widths, reflow into a vertical layout, keep controls usable, respect safe-area insets, and prevent horizontal page overflow.
- Keep headings, messages, action cards, and forms readable at normal zoom with comfortable line lengths, spacing, and hit areas.

### Light theme

- Use white and subtle cool-gray surfaces and restrained gradients.
- Use near-black/charcoal text with readable secondary text.
- Use charcoal/graphite primary actions with white labels.
- Keep assistant bubbles light/neutral; use a distinct but quiet green cue for human-agent replies.
- Make the theme toggle easy to see against a light header: solid surface, visible high-contrast icon and border, approximately 40×40 px hit area, hover/focus feedback, and an accessible name stating the action.

### Dark theme

- Use refined deep charcoal/navy panels, subtle surface separation, and visible borders.
- Use a restrained teal/cyan accent for interactive emphasis. Avoid a large, overly saturated or “wrong blue” surface.
- Keep customer, assistant, and human message roles distinguishable with softened variants of the same palette.
- Ensure input text, placeholders, secondary labels, speaker icons, borders, and focus rings remain visible.
- Persist the light/dark selection across reloads and between the customer and staff surfaces.

### Zen mode

Zen is an attention/layout mode as well as a palette:

- Reduce nonessential quick queries, promotional content, and visual clutter; soften cards and borders and allow the conversation more breathing room.
- Preserve the active account and chat; Zen must not restart the session.
- Keep essential account, language, light/dark, message speech, microphone, and text input controls available.
- Support both Zen light and Zen dark with readable text, cards, profile controls, and icons. Do not let inherited colors make content disappear.
- Use gentle or no animation; respect reduced-motion preferences.
- Keep the Zen button fixed in its header position before and after toggling. Always show the complete **“Zen mode”** label—do not move it or replace it with an emoji-only label.
- Persist Zen separately from light/dark theme.
- Slower speech is appropriate in Zen; it is not a replacement for normal text contrast.

### Accessibility details

- Use semantic controls, visible keyboard focus, localized button names, and state attributes for toggle/speech buttons.
- Keep status feedback for listening, waiting for an agent, and agent connected.
- Aim for at least 4.5:1 contrast for normal-size text and 3:1 for large text and important controls.
- Do not communicate financial terms, speaker state, consent, or human/AI identity by color alone.
- Maintain typed interaction if speech recognition is unavailable.

## 6. Other finalized product decisions

- **Quick voice** wording was changed to **Quick query**.
- Keep the microphone icon conventional and professional.
- Keep consent revocation only when useful, with an explicit confirmation; remove customer-facing audit-log controls because they are operational rather than customer actions.
- KYC support is a waiting-for-human flow. The customer remains in the existing chat while staff works in the separate inbox.
- The app is designed to work without a hosted AI agent key: local rules, parsing, mock data, and browser speech power this demo.
- Be clear that sample profiles, financial calculations, KFS details, policy data, signatures, and integrations are simulated. Do not invite customers to enter real financial or identity data.

## 7. Side-by-side comparison scorecard

Use the following checklist independently for this demo and the comparison demo. Mark each item **Pass**, **Partial**, or **Fail**, and record evidence (screen, viewport, or interaction). Give extra weight to the first four categories when judging a showcase.

| Category | Test | Saytm target |
|---|---|---|
| Voice correctness | Initial load speaks only the short welcome | Pass |
| Voice correctness | Switching language and theme speaks welcome in selected language | Pass |
| Voice correctness | “Saytm” sounds like “Say T M” | Pass |
| Voice correctness | Hindi “AI” sounds like “एआई,” not “अइ” | Pass |
| Voice control | Same message speaker stops its own active narration | Pass |
| Voice control | Starting a different message cancels the previous one | Pass |
| Voice control | Human replies stay silent unless manually played | Pass |
| Voice control | Hindi takeover announcement is both displayed and spoken in Hindi | Pass |
| Customer flow | First screen has no preselected customer/session | Pass |
| Customer flow | Choosing a profile starts chat without Continue | Pass |
| Customer flow | Desktop profile card and explanatory footer align cleanly | Pass |
| Customer flow | Phone profile control is in the top-right header | Pass |
| Human support | Customer stays in current chat while waiting | Pass |
| Human support | Staff reply area is hidden until join/intervention | Pass |
| Human support | Intervention pauses AI and makes transcript notice understandable | Pass |
| Messaging | Customer-side and operator-side left/right semantics are correct | Pass |
| Messaging | Customer, AI, and staff have distinct but coherent message treatments | Pass |
| Visual design | Desktop and phone are intentionally responsive without horizontal overflow | Pass |
| Visual design | Theme toggle is obvious in light mode | Pass |
| Visual design | Standard dark theme uses restrained charcoal/teal rather than harsh blue | Pass |
| Visual design | Zen changes attention/density, not only color | Pass |
| Visual design | Zen remains readable in both light and dark modes | Pass |
| Accessibility | Keyboard focus, reduced motion, labels, and text fallback work | Pass |
| Product clarity | Demo/mock/non-production status is clear | Pass |

### Optional numeric scoring

For a quick showcase comparison, assign each category a score from 1 to 5:

| Category | Weight | Demo A | Demo B | Notes/evidence |
|---|---:|---:|---:|---|
| Voice quality, language, and control | 25% |  |  |  |
| Customer journey clarity and trust | 20% |  |  |  |
| Staff handoff and operational usability | 15% |  |  |  |
| Responsive visual polish | 15% |  |  |  |
| Light/dark/Zen contrast and consistency | 15% |  |  |  |
| Accessibility and error handling | 10% |  |  |  |

Score on the same browser, device sizes, language, and test journeys. Keep notes on real observations; do not score a feature as passing merely because a button is visible.

## 8. Suggested comparison run

For each project, test the same sequence:

1. Load a fresh customer page. Confirm no customer is selected and listen to the welcome.
2. Switch Hindi → English and back; switch the theme. Confirm welcome speech follows the selected language.
3. Use the profile control on desktop and phone; confirm placement, alignment, and immediate chat start.
4. Start one assistant message, stop it from the same speaker control, then play another message.
5. In Hindi, trigger human intervention. Confirm the takeover notice is written in Hindi, “AI” is spoken as “एआई,” and the notice can be stopped from its speaker button.
6. Confirm human-agent replies do not auto-speak; play one manually.
7. Check the same transcript in staff view for correct sender alignment, role colors, and composer gating.
8. Inspect standard light, standard dark, Zen light, and Zen dark for clipped controls, unreadable text, and contrast problems.
9. Repeat at a common phone viewport and a desktop viewport; note overflow and misplaced controls.

## 9. Related project documentation

- [Full UI/UX design specification](./design.md)
- [Project setup and feature overview](./README.md)
- [Current feature status and limitations](./docs/FEATURE_STATUS.md)
- [Customer/staff workflows](./docs/WORKFLOW.md)
