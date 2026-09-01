"use client";

import { useState } from "react";
import { askPulse, PulseEvent } from "@/lib/api";

const PROMPTS = [
  "What needs attention right now?",
  "Summarize the latest critical events",
  "Which regions have the most activity?",
];

export default function AIAssistant({ events }: { events: PulseEvent[] }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("Ask Pulse anything about the events currently visible on the map.");
  const [loading, setLoading] = useState(false);

  async function submit(value = question) {
    const prompt = value.trim();
    if (!prompt || loading) return;
    setQuestion(prompt);
    setLoading(true);
    try {
      const response = await askPulse(prompt, events);
      setAnswer(response.answer);
    } catch {
      setAnswer("Pulse could not reach the intelligence service. Check the API connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="ai-card" aria-label="Pulse AI assistant">
      <div className="ai-card-topline">
        <div className="ai-orb" aria-hidden="true"><span>✦</span></div>
        <div>
          <div className="eyebrow eyebrow-bright">Pulse AI · Decision support</div>
          <h2>Ask the world what matters.</h2>
        </div>
        <span className="ai-status"><i /> Ready</span>
      </div>
      <p className="ai-description">Get a fast read on the events in your current view. Answers are grounded in the latest indexed pulse data.</p>
      <div className="prompt-row">
        {PROMPTS.map((prompt) => (
          <button key={prompt} type="button" onClick={() => submit(prompt)}>{prompt}</button>
        ))}
      </div>
      <form className="ai-input" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
        <span className="ai-input-icon">⌕</span>
        <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about a region, event, or emerging pattern…" aria-label="Ask Pulse AI" />
        <button type="submit" disabled={loading || !question.trim()}>{loading ? "Thinking…" : "Ask Pulse"}<span>↗</span></button>
      </form>
      <div className="ai-answer">
        <div className="answer-label"><span>✦</span> Pulse response</div>
        <p>{answer}</p>
      </div>
    </section>
  );
}

