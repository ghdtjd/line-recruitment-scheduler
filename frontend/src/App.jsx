import React, { useState, useEffect } from 'react';
import Calendar from './Calendar.jsx';
import Login from './Login.jsx';

function App() {
    const [userId, setUserId] = useState(localStorage.getItem('line_web_uid') || '');

    const handleLogin = (id) => {
        localStorage.setItem('line_web_uid', id);
        setUserId(id);
    };

    const handleLogout = () => {
        localStorage.removeItem('line_web_uid');
        setUserId('');
    };

    return (
        <div className="App">
            {userId ? (
                <Calendar uid={userId} onLogout={handleLogout} />
            ) : (
                <Login onLogin={handleLogin} />
            )}
        </div>
    );
}

export default App;
