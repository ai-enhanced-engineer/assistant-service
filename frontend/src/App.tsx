import { useEffect, useState } from 'react';
import './style.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState<string>('');

  useEffect(() => {
    fetch(`${API_URL}/start`)
      .then((res) => res.json())
      .then((data) => setThreadId(data.thread_id));
  }, []);

  const sendMessage = async () => {
    if (!input) return;
    const userMessage = input;
    setMessages([...messages, `You: ${userMessage}`]);
    setInput('');

    const resp = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, message: userMessage }),
    }).then((r) => r.json());

    setMessages((msgs) => [...msgs, `Assistant: ${resp.response}`]);
  };

  return (
    <div className="chat-container">
      <h1>Assistant Chat</h1>
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i}>{m}</div>
        ))}
      </div>
      <div className="input-row">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') sendMessage();
          }}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;
