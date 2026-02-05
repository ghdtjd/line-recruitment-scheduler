import React, { useState, useEffect } from 'react';
import liff from '@line/liff';
import axios from 'axios';
import './Calendar.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'; // Use relative path if proxied, or env var

const SCHEDULE_TYPES = [
    { code: 'ES_SUBMIT', name: 'ES提出', nameKo: 'ES 제출', color: '#FF6B6B' },
    { code: 'SPI_TEST', name: 'SPI試験', nameKo: 'SPI 테스트', color: '#4ECDC4' },
    { code: 'INTERVIEW_1', name: '一次面接', nameKo: '1차 면접', color: '#45B7D1' },
    { code: 'INTERVIEW_2', name: '二次面接', nameKo: '2차 면접', color: '#96CEB4' },
    { code: 'INTERVIEW_3', name: '三次面接', nameKo: '3차 면접', color: '#FFEAA7' },
    { code: 'FINAL_INTERVIEW', name: '最終面接', nameKo: '최종 면접', color: '#DDA15E' },
    { code: 'EXPLANATION', name: '会社説明会', nameKo: '회사 설명회', color: '#C9ADA7' },
    { code: 'INTERNSHIP', name: 'インターン', nameKo: '인턴십', color: '#B4A7D6' },
    { code: 'OTHER', name: 'その他', nameKo: '기타', color: '#90A4AE' }
];

function Calendar(props) {
    const [lineUID, setLineUID] = useState(props.uid || '');
    const [currentDate, setCurrentDate] = useState(new Date());
    const [schedules, setSchedules] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [selectedDate, setSelectedDate] = useState(null);
    const [modalMode, setModalMode] = useState('list'); // 'list' or 'create'
    const [formData, setFormData] = useState({
        type_code: 'ES_SUBMIT',
        company_name: '',
        schedule_time: '',
        location: '',
        memo: ''
    });
    const [isLiffInitialized, setIsLiffInitialized] = useState(false);

    useEffect(() => {
        if (props.uid) {
            setLineUID(props.uid);
            loadSchedules(props.uid);
            setIsLiffInitialized(true);
        } else {
            initializeLiff();
        }
    }, [props.uid]);

    const initializeLiff = async () => {
        try {
            // In local dev without LIFF ID, we might mock or skip
            const liffId = import.meta.env.VITE_LIFF_ID;
            if (liffId) {
                await liff.init({ liffId });
                if (liff.isLoggedIn()) {
                    const profile = await liff.getProfile();
                    setLineUID(profile.userId);
                    loadSchedules(profile.userId);
                } else {
                    liff.login();
                }
            } else {
                console.warn("LIFF ID not provided. Running in standalone mode.");
                // Fallback for local testing
                const testUid = 'test_user_1';
                setLineUID(testUid);
                loadSchedules(testUid);
            }
            setIsLiffInitialized(true);
        } catch (error) {
            console.error('LIFF initialization failed', error);
            // Fallback on error too
            const testUid = 'test_user_1';
            setLineUID(testUid);
            loadSchedules(testUid);
            setIsLiffInitialized(true);
        }
    };

    useEffect(() => {
        if (lineUID) {
            loadSchedules(lineUID);
        }
    }, [currentDate, lineUID]);

    const loadSchedules = async (uid) => {
        try {
            const yearMonth = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
            const response = await axios.get(`${API_BASE_URL}/schedules/${uid}?month=${yearMonth}`);
            setSchedules(response.data.schedules);
        } catch (error) {
            console.error('Failed to load schedules', error);
        }
    };

    const handleDateClick = (date) => {
        setSelectedDate(date);
        setModalMode('list');
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!lineUID) {
            alert("LINEにログインしてください。");
            return;
        }

        try {
            await axios.post(`${API_BASE_URL}/schedules`, {
                line_uid: lineUID,
                ...formData,
                // Fix: Use local date string construction
                schedule_date: selectedDate.getFullYear() + '-' +
                    String(selectedDate.getMonth() + 1).padStart(2, '0') + '-' +
                    String(selectedDate.getDate()).padStart(2, '0')
            });

            setShowModal(false);
            setFormData({
                type_code: 'ES_SUBMIT',
                company_name: '',
                schedule_time: '',
                location: '',
                memo: ''
            });

            loadSchedules(lineUID);

            // Optional: Close LIFF window
            // liff.closeWindow();
        } catch (error) {
            console.error('Failed to create schedule', error);
            alert('日程登録に失敗しました。');
        }
    };

    const formatTime = (timeStr) => {
        if (!timeStr) return '';
        const str = String(timeStr);
        if (str.includes(':')) {
            const [h, m] = str.split(':');
            return `${h}時 ${m}分`;
        }
        if (str.length >= 4 && !isNaN(str)) {
            return `${str.substring(0, 2)}時 ${str.substring(2, 4)}分`;
        }
        return str;
    };

    const renderCalendar = () => {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        const firstDay = new Date(year, month, 1);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const days = [];
        const currentDay = new Date(startDate);

        // 6 weeks to cover all possibilities (42 days)
        for (let i = 0; i < 42; i++) {
            // Create a new date object for the specific day to avoid reference issues
            const dateForRender = new Date(currentDay);

            // Fix: Use local date string construction to avoid timezone shift
            const dateStr = dateForRender.getFullYear() + '-' +
                String(dateForRender.getMonth() + 1).padStart(2, '0') + '-' +
                String(dateForRender.getDate()).padStart(2, '0');

            const daySchedules = schedules.filter(s => s.schedule_date === dateStr);
            const isOtherMonth = dateForRender.getMonth() !== month;

            days.push(
                <div
                    key={i}
                    className={`calendar-day ${isOtherMonth ? 'other-month' : ''}`}
                    onClick={() => handleDateClick(dateForRender)}
                >
                    <div className="day-number">{dateForRender.getDate()}</div>
                    <div className="day-schedules">
                        {daySchedules.map((schedule, idx) => {
                            const type = SCHEDULE_TYPES.find(t => t.code === schedule.type_code);
                            return (
                                <div
                                    key={idx}
                                    className="schedule-dot"
                                    style={{ backgroundColor: type?.color || '#999' }}
                                    title={`${schedule.company_name} - ${type?.name}`}
                                />
                            );
                        })}
                    </div>
                </div>
            );

            currentDay.setDate(currentDay.getDate() + 1);
        }

        return days;
    };

    if (!isLiffInitialized) return <div>Loading...</div>;

    return (
        <div className="calendar-container">
            <div className="calendar-header">
                <button onClick={() => setCurrentDate(new Date(currentDate.setMonth(currentDate.getMonth() - 1)))}>
                    ◀
                </button>
                <h2>{currentDate.getFullYear()}年 {currentDate.getMonth() + 1}月</h2>
                <button onClick={() => setCurrentDate(new Date(currentDate.setMonth(currentDate.getMonth() + 1)))}>
                    ▶
                </button>
            </div>

            <div className="calendar-weekdays">
                {['日', '月', '火', '水', '木', '金', '土'].map((day, index) => (
                    <div key={day} className={`weekday ${index === 0 ? 'sunday' : index === 6 ? 'saturday' : ''}`}>{day}</div>
                ))}
            </div>

            <div className="calendar-grid">
                {renderCalendar()}
            </div>

            {props.onLogout && (
                <div className="logout-container">
                    <button onClick={props.onLogout} className="logout-btn">
                        ログアウト
                    </button>
                </div>
            )}

            {showModal && (
                <div className="modal" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h3>{selectedDate.getFullYear()}年 {selectedDate.getMonth() + 1}月 {selectedDate.getDate()}日</h3>

                        {modalMode === 'list' ? (
                            <div className="schedule-list-view">
                                {schedules.filter(s => s.schedule_date === selectedDate.getFullYear() + '-' + String(selectedDate.getMonth() + 1).padStart(2, '0') + '-' + String(selectedDate.getDate()).padStart(2, '0')).length > 0 ? (
                                    <div className="schedule-list">
                                        {schedules.filter(s => s.schedule_date === selectedDate.getFullYear() + '-' + String(selectedDate.getMonth() + 1).padStart(2, '0') + '-' + String(selectedDate.getDate()).padStart(2, '0')).map((schedule, idx) => {
                                            const type = SCHEDULE_TYPES.find(t => t.code === schedule.type_code);
                                            return (
                                                <div key={idx} className="schedule-item" style={{ borderLeft: `4px solid ${type?.color || '#ccc'}` }}>
                                                    <div className="schedule-type-name">{type?.name}</div>
                                                    <div className="schedule-company">{schedule.company_name}</div>
                                                    <div className="schedule-time">⏰ {schedule.schedule_time ? formatTime(schedule.schedule_time) : '未定'}</div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <p className="no-schedules">予定はありません</p>
                                )}

                                <div className="modal-buttons">
                                    <button className="btn-submit" onClick={() => setModalMode('create')}>
                                        ＋ 予定を追加
                                    </button>
                                    <button className="btn-cancel" onClick={() => setShowModal(false)}>
                                        閉じる
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit}>
                                <label>
                                    種類
                                    <select
                                        value={formData.type_code}
                                        onChange={(e) => setFormData({ ...formData, type_code: e.target.value })}
                                        required
                                    >
                                        {SCHEDULE_TYPES.map(type => (
                                            <option key={type.code} value={type.code}>
                                                {type.name}
                                            </option>
                                        ))}
                                    </select>
                                </label>

                                <label>
                                    企業名
                                    <input
                                        type="text"
                                        value={formData.company_name}
                                        onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                                        required
                                        placeholder="例: トヨタ自動車"
                                    />
                                </label>

                                <label>
                                    時間
                                    <div className="time-selector">
                                        <select
                                            value={formData.schedule_time ? formData.schedule_time.split(':')[0] : ''}
                                            onChange={(e) => {
                                                const newHour = e.target.value;
                                                const currentMinute = formData.schedule_time ? formData.schedule_time.split(':')[1] : '00';
                                                setFormData({ ...formData, schedule_time: newHour ? `${newHour}:${currentMinute}` : '' });
                                            }}
                                            className="time-select"
                                        >
                                            <option value="">Hour</option>
                                            {Array.from({ length: 24 }, (_, i) => {
                                                const hour = String(i).padStart(2, '0');
                                                return <option key={hour} value={hour}>{hour}</option>;
                                            })}
                                        </select>
                                        <span>:</span>
                                        <select
                                            value={formData.schedule_time ? formData.schedule_time.split(':')[1] : ''}
                                            onChange={(e) => {
                                                const newMinute = e.target.value;
                                                const currentHour = formData.schedule_time ? formData.schedule_time.split(':')[0] : '09'; // Default to 09 if not set
                                                setFormData({ ...formData, schedule_time: currentHour ? `${currentHour}:${newMinute}` : `09:${newMinute}` });
                                            }}
                                            className="time-select"
                                        >
                                            <option value="">Minute</option>
                                            {Array.from({ length: 12 }, (_, i) => {
                                                const minute = String(i * 5).padStart(2, '0');
                                                return <option key={minute} value={minute}>{minute}</option>;
                                            })}
                                        </select>
                                    </div>
                                </label>

                                <label>
                                    場所
                                    <input
                                        type="text"
                                        value={formData.location}
                                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                        placeholder="例: 東京本社"
                                    />
                                </label>

                                <label>
                                    メモ
                                    <textarea
                                        value={formData.memo}
                                        onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                                        placeholder="準備するもの、注意事項など"
                                        rows="3"
                                    />
                                </label>

                                <div className="modal-buttons">
                                    <button type="submit" className="btn-submit">登録</button>
                                    <button type="button" onClick={() => setModalMode('list')} className="btn-cancel">
                                        戻る
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default Calendar;
