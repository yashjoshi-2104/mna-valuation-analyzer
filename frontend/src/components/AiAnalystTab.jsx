import { useEffect, useRef, useState } from 'react';
import { api } from '../api';

const QUICK_PROMPTS = [
  'Explain this valuation range in plain English',
  'Why are these companies good comparables?',
  'What are the biggest risks in this estimate?',
  'How would a lower EBITDA margin change the valuation?',
];

export default function AiAnalystTab({ companyId, companyName }) {
  const [messages, setMessages] = useState([]); // {role, content}
  const [input, setInput] = useState('');
  const [streamingText, setStreamingText] = useState(null); // in-progress assistant reply
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [lastAttempt, setLastAttempt] = useState(null);
  const scrollRef = useRef(null);

  // Reset the conversation when the selected company changes — old answers
  // about a different company would be confusing context to keep around.
  useEffect(() => {
    setMessages([]);
    setStreamingText(null);
    setError(null);
    setLastAttempt(null);
  }, [companyId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, streamingText]);

  const dispatch = (nextMessages) => {
    setSending(true);
    setError(null);
    setStreamingText('');

    api.chatStream(companyId, nextMessages, (_chunk, full) => setStreamingText(full))
      .then((full) => {
        setMessages((m) => [...m, { role: 'assistant', content: full }]);
        setStreamingText(null);
        setLastAttempt(null);
      })
      .catch((e) => {
        setError(e.message);
        setStreamingText(null);
        setLastAttempt(nextMessages);
      })
      .finally(() => setSending(false));
  };

  const send = (text) => {
    const content = text.trim();
    if (!content || sending || !companyId) return;
    const next = [...messages, { role: 'user', content }];
    setMessages(next);
    setInput('');
    dispatch(next);
  };

  const retry = () => {
    if (lastAttempt) dispatch(lastAttempt);
  };

  return (
    <div className="panel-block ai-tab">
      <div className="block-head">
        <div>
          <span className="eyebrow">Optional · local LLM via Ollama · grounded in this company's computed data only</span>
          <h2>AI Analyst — {companyName || '…'}</h2>
        </div>
      </div>

      <div className="chat-window" ref={scrollRef}>
        {messages.length === 0 && !streamingText && (
          <div className="chat-empty">
            <p>
              Ask about {companyName ? companyName + "'s" : "this company's"} comps or valuation.
              The model only ever sees numbers this app already computed — it explains,
              it doesn't calculate.
            </p>
            <div className="quick-prompts">
              {QUICK_PROMPTS.map((p) => (
                <button key={p} className="quick-prompt-btn" onClick={() => send(p)}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <span className="chat-role">{m.role === 'user' ? 'You' : 'AI Analyst'}</span>
            <p>{m.content}</p>
          </div>
        ))}

        {streamingText !== null && (
          <div className="chat-msg assistant">
            <span className="chat-role">AI Analyst</span>
            <p>
              {streamingText || <span className="chat-thinking">Thinking…</span>}
              {streamingText && <span className="chat-cursor" />}
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button className="retry-btn" onClick={retry}>Retry</button>
        </div>
      )}

      <form
        className="chat-input-row"
        onSubmit={(e) => { e.preventDefault(); send(input); }}
      >
        <input
          className="chat-input"
          placeholder={`Ask about ${companyName || 'this company'}…`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending || !companyId}
        />
        <button type="submit" className="ai-ask-btn" disabled={sending || !input.trim()}>
          {sending ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  );
}
