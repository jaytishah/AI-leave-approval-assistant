import React, { useState, useEffect, useCallback } from 'react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { adminApi } from '@/services/api';

// ── Types ──────────────────────────────────────────────────────────────────
interface AIUsageSummary {
    total_tokens: number;
    total_requests: number;
    prompt_tokens: number;
    output_tokens: number;
    tokens_today: number;
    requests_today: number;
    tokens_this_month: number;
    requests_this_month: number;
}

interface AIUsagePerEmployee {
    employee_id: number;
    employee_name: string;
    department: string | null;
    total_tokens: number;
    prompt_tokens: number;
    output_tokens: number;
    total_requests: number;
    last_request_at: string | null;
}

interface AIUsageDailyPoint {
    date: string;
    total_tokens: number;
    prompt_tokens: number;
    output_tokens: number;
    requests: number;
}

interface AIUsageByCallType {
    call_type: string;
    total_tokens: number;
    requests: number;
}

// ── Palette & Constants ────────────────────────────────────────────────────
const PROMPT_COLOR = '#6366f1';  // indigo
const OUTPUT_COLOR = '#22d3ee';  // cyan
const DONUT_COLORS = ['#6366f1', '#22d3ee', '#f59e0b', '#10b981'];

const CALL_TYPE_LABELS: Record<string, string> = {
    LEAVE_EVALUATION: 'Leave Evaluation',
    MEDICAL_CERT: 'Medical Certificate',
};

// ── Helpers ────────────────────────────────────────────────────────────────
function fmt(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
}

// ── Sub-components ─────────────────────────────────────────────────────────
function StatCard({
    label, value, sub,
}: { label: string; value: string | number; sub?: string }) {
    return (
        <div style={styles.statCard}>
            <span style={styles.statLabel}>{label}</span>
            <span style={styles.statValue}>{value}</span>
            {sub && <span style={styles.statSub}>{sub}</span>}
        </div>
    );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
    return <h4 style={styles.sectionTitle}>{children}</h4>;
}

// ── Main Component ─────────────────────────────────────────────────────────
const AIAnalyticsDashboard: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [dailyDays, setDailyDays] = useState(30);

    const [summary, setSummary] = useState<AIUsageSummary | null>(null);
    const [perEmployee, setPerEmployee] = useState<AIUsagePerEmployee[]>([]);
    const [daily, setDaily] = useState<AIUsageDailyPoint[]>([]);
    const [byCallType, setByCallType] = useState<AIUsageByCallType[]>([]);

    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const [sumData, empData, dayData, ctData] = await Promise.all([
                adminApi.getAIUsageSummary(),
                adminApi.getAIUsagePerEmployee(),
                adminApi.getAIUsageDaily(dailyDays),
                adminApi.getAIUsageByCallType(),
            ]);
            setSummary(sumData);
            setPerEmployee(empData);
            setDaily(dayData);
            setByCallType(ctData);
        } catch (e) {
            console.error('[AIAnalytics] fetch error', e);
        } finally {
            setLoading(false);
        }
    }, [dailyDays]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    // ── Loading skeleton ─────────────────────────────────────────────────────
    if (loading) {
        return (
            <div style={styles.wrapper}>
                <div style={styles.header}>
                    <span style={styles.headerIcon}>🤖</span>
                    <h3 style={styles.headerTitle}>AI Token Analytics</h3>
                </div>
                <div style={styles.skeletonGrid}>
                    {[0, 1, 2, 3].map(i => (
                        <div key={i} style={{ ...styles.statCard, ...styles.skeleton }} />
                    ))}
                </div>
                <div style={{ ...styles.chartBox, ...styles.skeleton, height: 220, marginTop: 24 }} />
            </div>
        );
    }

    // ── Empty state ──────────────────────────────────────────────────────────
    const hasData = summary && summary.total_requests > 0;
    if (!hasData) {
        return (
            <div style={styles.wrapper}>
                <div style={styles.header}>
                    <span style={styles.headerIcon}>🤖</span>
                    <h3 style={styles.headerTitle}>AI Token Analytics</h3>
                </div>
                <div style={styles.emptyState}>
                    <span style={{ fontSize: 48 }}>📊</span>
                    <p style={{ marginTop: 12, color: '#94a3b8' }}>
                        No AI usage data yet. Token usage will appear here after the first leave request is
                        processed by Gemini.
                    </p>
                </div>
            </div>
        );
    }

    const donutData = byCallType.map(d => ({
        name: CALL_TYPE_LABELS[d.call_type] ?? d.call_type,
        value: d.total_tokens,
    }));

    const topEmployees = perEmployee.slice(0, 10);

    return (
        <div style={styles.wrapper}>
            {/* Header */}
            <div style={styles.header}>
                <span style={styles.headerIcon}>🤖</span>
                <h3 style={styles.headerTitle}>AI Token Analytics</h3>
                <button onClick={fetchAll} style={styles.refreshBtn} title="Refresh">↺</button>
            </div>

            {/* Stat tiles */}
            <div style={styles.statGrid}>
                <StatCard label="All-time Tokens" value={fmt(summary!.total_tokens)} sub="total" />
                <StatCard label="All-time Requests" value={fmt(summary!.total_requests)} />
                <StatCard
                    label="Today"
                    value={fmt(summary!.tokens_today)}
                    sub={`${summary!.requests_today} req${summary!.requests_today !== 1 ? 's' : ''}`}
                />
                <StatCard
                    label="This Month"
                    value={fmt(summary!.tokens_this_month)}
                    sub={`${summary!.requests_this_month} req${summary!.requests_this_month !== 1 ? 's' : ''}`}
                />
                <StatCard label="Prompt Tokens" value={fmt(summary!.prompt_tokens)} sub="all-time" />
                <StatCard label="Output Tokens" value={fmt(summary!.output_tokens)} sub="all-time" />
            </div>

            {/* Daily trend + Call-type donut */}
            <div style={styles.rowTwo}>
                {/* Line chart */}
                <div style={{ ...styles.chartBox, flex: 2 }}>
                    <div style={styles.chartHeader}>
                        <SectionTitle>Daily Token Consumption</SectionTitle>
                        <select
                            value={dailyDays}
                            onChange={e => setDailyDays(Number(e.target.value))}
                            style={styles.select}
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={30}>Last 30 days</option>
                            <option value={90}>Last 90 days</option>
                        </select>
                    </div>
                    {daily.length === 0 ? (
                        <p style={styles.noData}>No data for this period.</p>
                    ) : (
                        <ResponsiveContainer width="100%" height={220}>
                            <LineChart data={daily} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                                    tickFormatter={d => d.slice(5)}
                                />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={fmt} />
                                <Tooltip
                                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                                    labelStyle={{ color: '#e2e8f0' }}
                                    formatter={(v: number | undefined, name: string | undefined) => [fmt(v ?? 0), name ?? '']}
                                />
                                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
                                <Line
                                    type="monotone" dataKey="prompt_tokens" name="Prompt" stroke={PROMPT_COLOR}
                                    strokeWidth={2} dot={false} activeDot={{ r: 4 }}
                                />
                                <Line
                                    type="monotone" dataKey="output_tokens" name="Output" stroke={OUTPUT_COLOR}
                                    strokeWidth={2} dot={false} activeDot={{ r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </div>

                {/* Donut chart */}
                <div style={{ ...styles.chartBox, flex: 1, minWidth: 220 }}>
                    <SectionTitle>By Call Type</SectionTitle>
                    {donutData.length === 0 ? (
                        <p style={styles.noData}>No data yet.</p>
                    ) : (
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie
                                    data={donutData} dataKey="value" nameKey="name"
                                    cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                                    paddingAngle={3}
                                >
                                    {donutData.map((_, idx) => (
                                        <Cell key={idx} fill={DONUT_COLORS[idx % DONUT_COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                                    formatter={(v: number | undefined) => [fmt(v ?? 0), 'tokens']}
                                />
                                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
                            </PieChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

            {/* Per-employee bar chart */}
            {topEmployees.length > 0 && (
                <div style={{ ...styles.chartBox, marginTop: 20 }}>
                    <SectionTitle>Top Employees by Token Usage</SectionTitle>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart
                            data={topEmployees}
                            layout="vertical"
                            margin={{ top: 4, right: 24, bottom: 4, left: 120 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                            <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={fmt} />
                            <YAxis
                                type="category" dataKey="employee_name"
                                tick={{ fill: '#e2e8f0', fontSize: 12 }} width={120}
                            />
                            <Tooltip
                                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                                labelStyle={{ color: '#e2e8f0' }}
                                formatter={(v: number | undefined, name: string | undefined) => [fmt(v ?? 0), name ?? '']}
                            />
                            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
                            <Bar dataKey="prompt_tokens" name="Prompt" stackId="a" fill={PROMPT_COLOR} radius={[0, 0, 0, 0]} />
                            <Bar dataKey="output_tokens" name="Output" stackId="a" fill={OUTPUT_COLOR} radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

// ── Styles ─────────────────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
    wrapper: {
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        borderRadius: 16,
        padding: '24px 28px',
        border: '1px solid #334155',
        color: '#e2e8f0',
        fontFamily: 'Inter, system-ui, sans-serif',
    },
    header: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        marginBottom: 20,
    },
    headerIcon: { fontSize: 22 },
    headerTitle: {
        margin: 0,
        fontSize: 18,
        fontWeight: 700,
        background: 'linear-gradient(90deg, #818cf8, #22d3ee)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        flex: 1,
    },
    refreshBtn: {
        background: 'transparent',
        border: '1px solid #475569',
        color: '#94a3b8',
        borderRadius: 8,
        width: 32,
        height: 32,
        cursor: 'pointer',
        fontSize: 18,
        lineHeight: '1',
    },
    statGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap: 12,
        marginBottom: 24,
    },
    skeletonGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap: 12,
        marginBottom: 24,
    },
    statCard: {
        background: '#1e293b',
        borderRadius: 12,
        padding: '14px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        border: '1px solid #334155',
    },
    statLabel: { fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' },
    statValue: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
    statSub: { fontSize: 11, color: '#64748b' },
    rowTwo: {
        display: 'flex',
        gap: 16,
        flexWrap: 'wrap',
    },
    chartBox: {
        background: '#1e293b',
        borderRadius: 12,
        padding: '16px 20px',
        border: '1px solid #334155',
    },
    chartHeader: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 8,
    },
    sectionTitle: {
        margin: '0 0 12px',
        fontSize: 13,
        fontWeight: 600,
        color: '#94a3b8',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
    },
    select: {
        background: '#0f172a',
        border: '1px solid #334155',
        color: '#e2e8f0',
        borderRadius: 6,
        padding: '4px 8px',
        fontSize: 12,
        cursor: 'pointer',
    },
    noData: { color: '#64748b', fontSize: 13, textAlign: 'center', padding: '40px 0' },
    emptyState: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '48px 0',
        textAlign: 'center',
    },
    skeleton: {
        background: 'linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
        height: 80,
    },
};

export default AIAnalyticsDashboard;
