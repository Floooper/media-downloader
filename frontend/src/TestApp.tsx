import React from 'react';

function TestApp() {
  console.log('🧪 TestApp rendering...');
  
  return (
    <div style={{ padding: '20px', background: 'white', minHeight: '100vh' }}>
      <h1>✅ React is working!</h1>
      <p>If you can see this, React is rendering correctly.</p>
      
      <div style={{ 
        border: '1px solid #ccc', 
        padding: '10px', 
        marginTop: '20px',
        backgroundColor: '#f0f0f0'
      }}>
        <h3>System Status:</h3>
        <ul>
          <li>React: ✅ Working</li>
          <li>TypeScript: ✅ Working</li>
          <li>Vite: ✅ Working</li>
          <li>Time: {new Date().toLocaleString()}</li>
        </ul>
      </div>
      
      <button 
        onClick={() => alert('Button clicked!')}
        style={{ 
          padding: '10px 20px', 
          margin: '10px', 
          cursor: 'pointer',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px'
        }}
      >
        Test Button
      </button>
    </div>
  );
}

export default TestApp;
