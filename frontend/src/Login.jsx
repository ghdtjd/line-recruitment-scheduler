import React, { useState } from 'react';
import './Login.css';

function Login({ onLogin }) {
    const [userId, setUserId] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (userId.trim()) {
            onLogin(userId.trim());
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h1>취업 알림 (WEB)</h1>
                <p>사용할 ID를 입력해주세요.</p>
                <form onSubmit={handleSubmit}>
                    <input
                        type="text"
                        placeholder="User ID (예: user123)"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        required
                    />
                    <button type="submit">시작하기</button>
                    <p className="note">
                        * 이 ID는 사용자를 구분하는 용도로만 사용됩니다.<br/>
                        * 비밀번호가 없으니 타인이 추측하기 어려운 ID를 사용하세요.
                    </p>
                </form>
            </div>
        </div>
    );
}

export default Login;
