// Sidebar Component - Direct port from Sidebar.svelte
import { useState, useRef, useEffect, useCallback } from 'react';
import { ROW_COUNT_OPTIONS, AUTO_BET_INTERVAL_MS, getBinColors } from './constants';
import './Sidebar.css';
import { Tooltip, Tag, InputNumber, Button, Typography } from 'antd';
import { TrophyOutlined, StarOutlined, FireOutlined } from '@ant-design/icons';

const { Text } = Typography;

function Sidebar({
    balance,
    betAmount,
    setBetAmount,
    rowCount,
    setRowCount,
    riskLevel,
    setRiskLevel,
    hasOutstandingBalls,
    onDropBall,
    onSettingsClick,
    onStatsClick,
    isSettingsOpen,
    isStatsOpen,
    // Plinko-specific props
    selectedBallType,
    setSelectedBallType,
    ballTypes,
    currentBall,
    lastWin,
    winRecords,
    currentStreak,
    maxStreak,
}) {
    const [betMode, setBetMode] = useState('manual'); // 'manual' | 'auto'
    const [autoBetInput, setAutoBetInput] = useState(0);
    const [autoBetsLeft, setAutoBetsLeft] = useState(null);
    const [isAutoBetting, setIsAutoBetting] = useState(false);
    const autoBetTickRunningRef = useRef(false);
    const autoBetSessionRef = useRef(0);

    // Validation
    const isBetAmountNegative = betAmount < 0;
    const isBetExceedBalance = betAmount > balance;
    const isAutoBetInputNegative = autoBetInput < 0;
    const isDropBallDisabled = isBetAmountNegative || isBetExceedBalance || isAutoBetInputNegative;

    // Auto bet drop ball
    const autoBetDropBall = useCallback(async () => {
        if (autoBetTickRunningRef.current) return;
        autoBetTickRunningRef.current = true;

        const session = autoBetSessionRef.current;
        try {
            const result = await onDropBall?.(() => session !== autoBetSessionRef.current);
            if (result === 'insufficient-funds') {
                setIsAutoBetting(false);
            } else if (result === 'dropped' && autoBetsLeft !== null) {
                setAutoBetsLeft(prev => prev - 1);
            }
        } finally {
            autoBetTickRunningRef.current = false;
        }
    }, [autoBetsLeft, isAutoBetting, onDropBall]);

    // Start/stop auto bet interval
    useEffect(() => {
        if (!isAutoBetting) return;

        const intervalId = setInterval(autoBetDropBall, AUTO_BET_INTERVAL_MS);
        return () => clearInterval(intervalId);
    }, [isAutoBetting, autoBetDropBall]);

    useEffect(() => {
        if (autoBetsLeft === 0) setIsAutoBetting(false);
    }, [autoBetsLeft]);

    const handleBetClick = () => {
        if (betMode === 'manual') {
            onDropBall?.();
        } else if (isAutoBetting) {
            autoBetSessionRef.current++;
            setIsAutoBetting(false);
            setAutoBetsLeft(null);
        } else {
            autoBetSessionRef.current++;
            setAutoBetsLeft(autoBetInput === 0 ? null : autoBetInput);
            setIsAutoBetting(true);
        }
    };

    const handleBetAmountChange = (e) => {
        const value = parseFloat(e.target.value);
        setBetAmount(isNaN(value) ? 0 : value);
    };

    const handleAutoBetInputChange = (e) => {
        const value = parseInt(e.target.value);
        setAutoBetInput(isNaN(value) ? 0 : value);
    };

    const riskLevels = [
        { value: 'low', label: 'Low' },
        { value: 'medium', label: 'Medium' },
        { value: 'high', label: 'High' },
    ];

    return (
        <div className="sidebar">
            {/* Bet Mode Tabs */}
            <div className="bet-mode-tabs">
                <button
                    className={`bet-mode-tab ${betMode === 'manual' ? 'active' : ''}`}
                    onClick={() => setBetMode('manual')}
                    disabled={isAutoBetting}
                >
                    Manual
                </button>
                <button
                    className={`bet-mode-tab ${betMode === 'auto' ? 'active' : ''}`}
                    onClick={() => setBetMode('auto')}
                    disabled={isAutoBetting}
                >
                    Auto
                </button>
            </div>

            {/* Bet Amount */}
            <div className="form-group">
                <div className="form-header">
                    <label htmlFor="betAmount" className="form-label" style={{ margin: 0 }}>Bet Amount</label>
                    <Text type="secondary" style={{ margin: 0 }}>KSh {(betAmount ?? 0).toFixed(2)}</Text>
                </div>
                <div className="input-row">
                    <InputNumber
                        id="betAmount"
                        value={betAmount}
                        onChange={(val) => setBetAmount(isNaN(Number(val)) ? 0 : Number(val))}
                        min={0}
                        step={0.01}
                        disabled={isAutoBetting}
                        style={{ flex: 1 }}
                        controls={false}
                        formatter={(v) => `${v}`}
                        parser={(v) => v.replace(/\$\s?|(,*)/g, '')}
                        addonBefore={<div className="btc-icon">KSh </div>}
                    />
                    <Button.Group>
                        <Button
                            onClick={() => setBetAmount(prev => parseFloat((Number(prev || 0) / 2).toFixed(2)))}
                            disabled={isAutoBetting}
                        >
                            ½
                        </Button>
                        <Button
                            onClick={() => setBetAmount(prev => parseFloat((Number(prev || 0) * 2).toFixed(2)))}
                            disabled={isAutoBetting}
                        >
                            2×
                        </Button>
                    </Button.Group>
                </div>
                {isBetAmountNegative && (
                    <p className="error-text">This must be greater than or equal to 0.</p>
                )}
                {isBetExceedBalance && (
                    <p className="error-text">Can't bet more than your balance!</p>
                )}
            </div>

            {/* Risk Level */}
            <div className="form-group mobile-sheet-secondary">
                <label htmlFor="riskLevel" className="form-label">Risk</label>
                <select
                    id="riskLevel"
                    value={riskLevel}
                    onChange={(e) => setRiskLevel(e.target.value)}
                    disabled={hasOutstandingBalls || isAutoBetting}
                    className="form-select"
                >
                    {riskLevels.map(({ value, label }) => (
                        <option key={value} value={value}>{label}</option>
                    ))}
                </select>
            </div>

            {/* Row Count */}
            <div className="form-group mobile-sheet-secondary">
                <label htmlFor="rowCount" className="form-label">Rows</label>
                <select
                    id="rowCount"
                    value={rowCount}
                    onChange={(e) => setRowCount(parseInt(e.target.value))}
                    disabled={hasOutstandingBalls || isAutoBetting}
                    className="form-select"
                >
                    {ROW_COUNT_OPTIONS.map((value) => (
                        <option key={value} value={value}>{value}</option>
                    ))}
                </select>
            </div>

            {/* Auto Bet Input */}
            {betMode === 'auto' && (
                <div className="form-group mobile-sheet-secondary">
                    <div className="form-label-row">
                        <label htmlFor="autoBetInput" className="form-label">Number of Bets</label>
                        <span className="help-icon" title="Enter '0' for unlimited bets.">?</span>
                    </div>
                    <div className="auto-bet-input">
                        <input
                            id="autoBetInput"
                            type="number"
                            value={isAutoBetting ? (autoBetsLeft ?? 0) : autoBetInput}
                            onChange={handleAutoBetInputChange}
                            disabled={isAutoBetting}
                            min="0"
                            inputMode="numeric"
                            className={isAutoBetInputNegative ? 'error' : ''}
                        />
                        {autoBetInput === 0 && !isAutoBetting && (
                            <span className="infinity-icon">∞</span>
                        )}
                    </div>
                    {isAutoBetInputNegative && (
                        <p className="error-text">This must be greater than or equal to 0.</p>
                    )}
                </div>
            )}

            {/* Bet Button */}
            <button
                className={`bet-button ${isAutoBetting ? 'stop' : ''}`}
                onClick={handleBetClick}
                disabled={isDropBallDisabled}
            >
                {betMode === 'manual' ? 'Drop Ball' : isAutoBetting ? 'Stop Autobet' : 'Start Autobet'}
            </button>

            {/* Footer */}
            <div className="sidebar-footer mobile-sheet-secondary">
                <div className="footer-buttons">
                    <button
                        className={`footer-btn ${isSettingsOpen ? 'active' : ''}`}
                        onClick={onSettingsClick}
                        title="Game Settings"
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 15.5A3.5 3.5 0 0 1 8.5 12 3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5m7.43-2.53c.04-.32.07-.64.07-.97 0-.33-.03-.66-.07-1l2.11-1.63c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.31-.61-.22l-2.49 1c-.52-.39-1.06-.73-1.69-.98l-.37-2.65A.506.506 0 0 0 14 2h-4c-.25 0-.46.18-.5.42l-.37 2.65c-.63.25-1.17.59-1.69.98l-2.49-1c-.22-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64L4.57 11c-.04.34-.07.67-.07 1 0 .33.03.65.07.97l-2.11 1.66c-.19.15-.25.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1.01c.52.4 1.06.74 1.69.99l.37 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.37-2.65c.63-.26 1.17-.59 1.69-.99l2.49 1.01c.22.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.66z" />
                        </svg>
                    </button>
                    <button
                        className={`footer-btn ${isStatsOpen ? 'active' : ''}`}
                        onClick={onStatsClick}
                        title="Live Stats"
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M16 11.78l4.24-7.33 1.73 1-5.23 9.05-6.51-3.75L5.46 19H22v2H2V3h2v14.54L9.5 8z" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* --- Plinko extra: Ball Selector, Last Win, Streak --- */}
            <div className="ball-selector-card sidebar-card mobile-sheet-secondary">
                <div className="ball-selector-header">
                    <StarOutlined />
                    <span>Ball Type</span>
                </div>
                <div className="ball-types-grid">
                    {Object.values(ballTypes || {}).map(ball => (
                        <Tooltip
                            key={ball.id}
                            title={
                                <div>
                                    <div style={{ fontWeight: 600 }}>{ball.name}</div>
                                    <div>{ball.description}</div>
                                    <div style={{ color: 'var(--text-secondary)' }}>Cost: {ball.cost}× bet</div>
                                </div>
                            }
                        >
                            <div
                                className={`ball-type-option ${selectedBallType === ball.id ? 'selected' : ''}`}
                                onClick={() => setSelectedBallType?.(ball.id)}
                                style={{ '--ball-color': ball.color }}
                            >
                                <div
                                    className="ball-color-circle"
                                    style={{ backgroundImage: `url(${ball.image})`, backgroundSize: 'cover', backgroundColor: 'transparent' }}
                                ></div>
                                <div className="ball-type-content">
                                    <div className="ball-type-name">{ball.name}</div>
                                    <div className="ball-type-cost">{ball.cost}×</div>
                                </div>
                            </div>
                        </Tooltip>
                    ))}
                </div>
            </div>

            {/* Last Win card removed as requested */}

            {/* Streak UI moved to History & Statistics */}
        </div>
    );
}

export default Sidebar;
