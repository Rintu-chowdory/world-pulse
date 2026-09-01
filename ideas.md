# World Pulse — Design Direction

## Three possible directions

### Theme Name: Meridian Command
Very Brief Intro: A dark editorial situation room where geographic signals, live data, and human judgment share one visual language. The mood is precise, calm, and operational rather than theatrical.
Probability: 0.07

### Theme Name: Atlas Paper
Very Brief Intro: A light cartographic journal with warm paper tones, ink-like lines, and annotated event cards. The mood is investigative and human, suited to slower reading and context.
Probability: 0.03

### Theme Name: Signal Bloom
Very Brief Intro: A restrained dark interface with luminous signal traces and warm alert colors that make changing global conditions legible at a glance. The mood is urgent but controlled.
Probability: 0.09

## Chosen approach: Meridian Command

### Design Movement
Contemporary information design informed by editorial cartography, aviation dashboards, and modernist Swiss wayfinding. The interface should feel like a composed operations desk, not a generic SaaS dashboard.

### Core Principles
1. Establish hierarchy through typography, alignment, and signal color instead of heavy cards.
2. Use asymmetry: a strong left rail, a dominant map field, and a narrow intelligence column.
3. Keep live information calm and legible; urgency is reserved for severity, not decoration.
4. Pair technical density with editorial breathing room so context remains readable.

### Color Philosophy
The base is near-black blue slate, chosen to recede behind geographic information. A mineral teal acts as the signature brand color: it suggests latitude lines, stable systems, and a cool analytical mind. Signal colors are functional: amber for watch, coral for high attention, and ice blue for neutral context. Avoid purple gradients and decorative neon.

### Layout Paradigm
Use a command-room composition: fixed rail, wide map/situation field, and a vertically stacked intelligence rail. On small screens the rail becomes a compact top band and the intelligence sections become horizontally scrollable modules. The page should not default to a centered marketing container.

### Signature Elements
1. A thin meridian line motif with small coordinate ticks.
2. Event severity shown as compact signal bars and rings rather than large badges.
3. A quiet grain and contour-line texture behind the map field.

### Interaction Philosophy
Interactions should feel like operating instruments: direct, reversible, and low-drama. Filters update the evidence field quickly, selected events remain visibly anchored, and hover states reveal context without causing layout shifts.

### Animation
Use short 160–240ms transitions for controls and list selection. Let live events enter with a subtle opacity/translate transition, never a bouncing notification. Respect reduced-motion preferences. Pulse indicators may breathe slowly, but the rest of the interface should remain still enough for scanning.

### Typography System
Use Space Grotesk for headlines, labels, and compact numeric readouts; use IBM Plex Sans for body copy and explanations. Headlines are tight and declarative. Metadata is uppercase with generous tracking. Body copy stays at 14–16px with comfortable line height.

### Brand Essence
World Pulse is a live global event intelligence desk for people who need the signal before the noise, distinguished by context-aware mapping and a calm operational interface.

Personality: observant, composed, exacting.

### Brand Voice
Headlines are concise and situation-oriented. CTAs describe the action and its payoff. Microcopy sounds like an analyst briefing a capable colleague.

Example lines:
- “See the pressure points before they become headlines.”
- “Ask Pulse AI to explain what changed.”

### Wordmark & Logo
A compact compass-meridian mark: a circular latitude arc interrupted by a vertical pulse stroke, with one offset dot marking the current signal. The mark should work without text and remain recognizable at favicon size.

### Signature Brand Color
Meridian Teal — #58D6C1. It is cool, ownable, and readable against the near-black slate without relying on glow effects.

## Style Decisions

- The frontend will use a dark, asymmetric command-center composition.
- The existing World Pulse information architecture and live API behavior are the ground truth.
- The Manus-hosted frontend will use the Render API at `https://world-pulse-api.onrender.com`.
- Decorative imagery will support the map/signal atmosphere, but data remains rendered as interface content rather than baked into images.
