const { useEffect, useMemo, useState } = React;

const API_BASE = "";
const TOKEN_KEY = "faculty_token";
const USER_KEY = "faculty_user";

function getRouteFromPath() {
    const path = window.location.pathname.toLowerCase();
    if (path.includes("students")) return "students";
    if (path.includes("attendance")) return "attendance";
    if (path.includes("marks")) return "marks";
    if (path.includes("reports")) return "reports";
    if (path.includes("dashboard")) return "dashboard";
    return "login";
}

function apiRequest(path, options = {}, token) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    return fetch(`${API_BASE}${path}`, { ...options, headers }).then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data?.error || data?.message || "Request failed");
        }
        return data;
    });
}

function EmptyState({ message }) {
    return <div className="empty-state">{message}</div>;
}

function Pagination({ pagination, onPage }) {
    if (!pagination) return null;
    return (
        <div className="pagination-bar">
            <span>{pagination.total} records</span>
            <div className="btn-group">
                <button className="btn btn-sm btn-outline-secondary" disabled={pagination.page <= 1} onClick={() => onPage(pagination.page - 1)}>Previous</button>
                <button className="btn btn-sm btn-outline-secondary" disabled>{pagination.page} / {pagination.total_pages}</button>
                <button className="btn btn-sm btn-outline-secondary" disabled={pagination.page >= pagination.total_pages} onClick={() => onPage(pagination.page + 1)}>Next</button>
            </div>
        </div>
    );
}

function Toasts({ toasts, onRemove }) {
    return (
        <div className="toast-stack">
            {toasts.map((toast) => (
                <div key={toast.id} className={`toast-item toast-${toast.type}`}>
                    <div>
                        <strong>{toast.title}</strong>
                        <div>{toast.message}</div>
                    </div>
                    <button onClick={() => onRemove(toast.id)} className="toast-close">x</button>
                </div>
            ))}
        </div>
    );
}

function Loader({ show }) {
    if (!show) return null;
    return (
        <div className="page-loader">
            <div className="loader-panel">
                <div className="spinner-border text-light" role="status"></div>
                <p className="mt-3 mb-0 text-light fw-semibold">Loading workspace...</p>
            </div>
        </div>
    );
}

function PageHeader({ eyebrow, title, description }) {
    return (
        <div className="page-header glass-card fade-in-up">
            <span className="page-eyebrow">{eyebrow}</span>
            <h2 className="page-title">{title}</h2>
            <p className="page-description">{description}</p>
        </div>
    );
}

function MetricCard({ label, value, tone = "default", detail }) {
    return (
        <div className={`metric-card metric-${tone}`}>
            <span className="metric-label">{label}</span>
            <h3 className="metric-value">{value}</h3>
            {detail ? <small className="metric-detail">{detail}</small> : null}
        </div>
    );
}

function DataCard({ title, subtitle, children }) {
    return (
        <section className="panel-card data-card fade-in-up">
            <div className="data-card-head">
                <h5>{title}</h5>
                {subtitle ? <p>{subtitle}</p> : null}
            </div>
            {children}
        </section>
    );
}

function LoginView({ onLogin, loading }) {
    const [loginMode, setLoginMode] = useState("email");
    const [email, setEmail] = useState("");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    return (
        <div className="login-page">
            <div className="login-backdrop"></div>
            <div className="login-shell fade-in-up">
                <section className="login-story">
                    <div className="story-badge">Academic Operations Suite</div>
                    <img src="/frontend/assets/logo.svg" alt="Faculty Analytics" className="login-logo" />
                    <h1>Faculty Analytics</h1>
                    <p>Professional academic monitoring for student records, attendance signals, and performance intelligence.</p>
                    <div className="story-grid">
                        <div className="story-stat"><strong>Students</strong><span>Clean record control</span></div>
                        <div className="story-stat"><strong>Attendance</strong><span>Risk visibility</span></div>
                        <div className="story-stat"><strong>Reports</strong><span>Presentation-ready insights</span></div>
                    </div>
                </section>
                <section className="login-panel">
                    <span className="panel-kicker">Secure Sign In</span>
                    <h3>Access faculty workspace</h3>
                    <p className="panel-copy">Use your institutional credentials to continue.</p>
                    <div className="mode-switcher">
                        <button className={loginMode === "email" ? "active" : ""} onClick={() => setLoginMode("email")} type="button">Email</button>
                        <button className={loginMode === "username" ? "active" : ""} onClick={() => setLoginMode("username")} type="button">Username</button>
                    </div>
                    <div className="form-stack">
                        {loginMode === "email" ? (
                            <label className="field-block">
                                <span>Email</span>
                                <input className="form-control" value={email} onChange={(e) => setEmail(e.target.value)} />
                            </label>
                        ) : (
                            <label className="field-block">
                                <span>Username</span>
                                <input className="form-control" value={username} onChange={(e) => setUsername(e.target.value)} />
                            </label>
                        )}
                        <label className="field-block">
                            <span>Password</span>
                            <input className="form-control" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                        </label>
                    </div>
                    <button disabled={loading} className="btn btn-dark w-100 login-button" onClick={() => onLogin({ login_mode: loginMode, email, username, password })}>
                        {loading ? "Signing in..." : "Enter Dashboard"}
                    </button>
                </section>
            </div>
        </div>
    );
}

function StudentsView({ token, notify, setLoading }) {
    const [rows, setRows] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [q, setQ] = useState("");
    const [dept, setDept] = useState("");
    const [page, setPage] = useState(1);
    const [pagination, setPagination] = useState(null);
    const [form, setForm] = useState({ roll: "", name: "", dept: "" });

    function loadData() {
        setLoading(true);
        apiRequest(`/api/students?q=${encodeURIComponent(q)}&dept=${encodeURIComponent(dept)}&page=${page}&per_page=8`, {}, token)
            .then((data) => {
                setRows(data.students || []);
                setDepartments(data.departments || []);
                setPagination(data.pagination);
            })
            .catch((err) => notify(err.message, "error", "Students"))
            .finally(() => setLoading(false));
    }

    useEffect(() => { loadData(); }, [q, dept, page]);

    function addStudent() {
        setLoading(true);
        apiRequest("/api/students", { method: "POST", body: JSON.stringify(form) }, token)
            .then(() => {
                notify("Student record created successfully.", "success", "Students");
                setForm({ roll: "", name: "", dept: "" });
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Students"))
            .finally(() => setLoading(false));
    }

    return (
        <div className="page-grid">
            <PageHeader eyebrow="Student Directory" title="Manage student records" description="Search departments, add new learners, and keep the academic roster clean." />
            <DataCard title="Directory Controls" subtitle="Filter and add student entries from one place.">
                <div className="control-grid">
                    <label className="field-block">
                        <span>Search by name or roll</span>
                        <input className="form-control" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
                    </label>
                    <label className="field-block">
                        <span>Department</span>
                        <select className="form-select" value={dept} onChange={(e) => { setPage(1); setDept(e.target.value); }}>
                            <option value="">All Departments</option>
                            {departments.map((item) => <option key={item} value={item}>{item}</option>)}
                        </select>
                    </label>
                </div>
                <div className="entry-grid">
                    <input className="form-control" placeholder="Roll No" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} />
                    <input className="form-control" placeholder="Student Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                    <input className="form-control" placeholder="Department" value={form.dept} onChange={(e) => setForm({ ...form, dept: e.target.value })} />
                    <button className="btn btn-dark" onClick={addStudent}>Add Student</button>
                </div>
            </DataCard>
            <DataCard title="Student Records" subtitle="Current roster across departments.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>Roll No</th><th>Name</th><th>Department</th></tr></thead>
                        <tbody>
                            {rows.length ? rows.map((row) => (
                                <tr key={row.roll_no}>
                                    <td><span className="table-chip">{row.roll_no}</span></td>
                                    <td>{row.name}</td>
                                    <td>{row.dept}</td>
                                </tr>
                            )) : <tr><td colSpan="3"><EmptyState message="No student records match the current filter." /></td></tr>}
                        </tbody>
                    </table>
                </div>
                <Pagination pagination={pagination} onPage={setPage} />
            </DataCard>
        </div>
    );
}

function AttendanceView({ token, notify, setLoading }) {
    const [rows, setRows] = useState([]);
    const [page, setPage] = useState(1);
    const [pagination, setPagination] = useState(null);
    const [summary, setSummary] = useState({ overall_percentage: 0, low_attendance_count: 0, total_attendance_rows: 0 });
    const [form, setForm] = useState({ roll: "", total: "", present: "" });

    function loadData() {
        setLoading(true);
        apiRequest(`/api/attendance?page=${page}&per_page=8`, {}, token)
            .then((data) => {
                setRows(data.data || []);
                setPagination(data.pagination);
                setSummary({
                    overall_percentage: data.overall_percentage || 0,
                    low_attendance_count: data.low_attendance_count || 0,
                    total_attendance_rows: data.total_attendance_rows || 0
                });
            })
            .catch((err) => notify(err.message, "error", "Attendance"))
            .finally(() => setLoading(false));
    }

    useEffect(() => { loadData(); }, [page]);

    function addAttendance() {
        setLoading(true);
        apiRequest("/api/attendance", { method: "POST", body: JSON.stringify(form) }, token)
            .then(() => {
                notify("Attendance record saved successfully.", "success", "Attendance");
                setForm({ roll: "", total: "", present: "" });
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Attendance"))
            .finally(() => setLoading(false));
    }

    return (
        <div className="page-grid">
            <PageHeader eyebrow="Attendance Tracker" title="Track class participation" description="Monitor class presence, identify weak attendance early, and maintain a clean log." />
            <div className="metrics-grid">
                <MetricCard label="Overall Attendance" value={`${summary.overall_percentage}%`} tone="emerald" detail="Institution-wide view" />
                <MetricCard label="Low Attendance Cases" value={summary.low_attendance_count} tone="rose" detail="Below 75 percent" />
                <MetricCard label="Total Records" value={summary.total_attendance_rows} tone="slate" detail="Attendance rows captured" />
            </div>
            <DataCard title="Add Attendance Row" subtitle="Record the latest attendance values.">
                <div className="entry-grid">
                    <input className="form-control" placeholder="Roll No" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} />
                    <input className="form-control" placeholder="Total Classes" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })} />
                    <input className="form-control" placeholder="Present Classes" value={form.present} onChange={(e) => setForm({ ...form, present: e.target.value })} />
                    <button className="btn btn-dark" onClick={addAttendance}>Save Attendance</button>
                </div>
            </DataCard>
            <DataCard title="Attendance Register" subtitle="Paginated attendance history for review.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>ID</th><th>Roll No</th><th>Total</th><th>Present</th><th>Percentage</th></tr></thead>
                        <tbody>
                            {rows.length ? rows.map((row) => (
                                <tr key={row.id}>
                                    <td>{row.id}</td>
                                    <td><span className="table-chip">{row.roll_no}</span></td>
                                    <td>{row.total}</td>
                                    <td>{row.present}</td>
                                    <td>{row.percentage}%</td>
                                </tr>
                            )) : <tr><td colSpan="5"><EmptyState message="No attendance entries available yet." /></td></tr>}
                        </tbody>
                    </table>
                </div>
                <Pagination pagination={pagination} onPage={setPage} />
            </DataCard>
        </div>
    );
}

function MarksView({ token, notify, setLoading }) {
    const [rows, setRows] = useState([]);
    const [q, setQ] = useState("");
    const [page, setPage] = useState(1);
    const [pagination, setPagination] = useState(null);
    const [stats, setStats] = useState({ avg_marks: 0, high_scorers: 0, subject_count: 0, total_marks_rows: 0 });
    const [form, setForm] = useState({ roll: "", subject: "", marks: "" });

    function loadData() {
        setLoading(true);
        apiRequest(`/api/marks?q=${encodeURIComponent(q)}&page=${page}&per_page=8`, {}, token)
            .then((data) => {
                setRows(data.data || []);
                setPagination(data.pagination);
                setStats({
                    avg_marks: data.avg_marks || 0,
                    high_scorers: data.high_scorers || 0,
                    subject_count: data.subject_count || 0,
                    total_marks_rows: data.total_marks_rows || 0
                });
            })
            .catch((err) => notify(err.message, "error", "Marks"))
            .finally(() => setLoading(false));
    }

    useEffect(() => { loadData(); }, [q, page]);

    function addMarks() {
        setLoading(true);
        apiRequest("/api/marks", { method: "POST", body: JSON.stringify(form) }, token)
            .then(() => {
                notify("Marks saved successfully.", "success", "Marks");
                setForm({ roll: "", subject: "", marks: "" });
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Marks"))
            .finally(() => setLoading(false));
    }

    return (
        <div className="page-grid">
            <PageHeader eyebrow="Marks Ledger" title="Manage subject scores" description="Search performance, record subject marks, and monitor strong and weak trends." />
            <div className="metrics-grid">
                <MetricCard label="Average Marks" value={stats.avg_marks} tone="blue" detail="Across current filter" />
                <MetricCard label="High Scorers" value={stats.high_scorers} tone="amber" detail="Scores 90 and above" />
                <MetricCard label="Subjects" value={stats.subject_count} tone="slate" detail={`${stats.total_marks_rows} total entries`} />
            </div>
            <DataCard title="Search and Add Marks" subtitle="Keep assessment data current and searchable.">
                <div className="control-grid">
                    <label className="field-block field-wide">
                        <span>Search by roll or subject</span>
                        <input className="form-control" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
                    </label>
                </div>
                <div className="entry-grid entry-grid-marks">
                    <input className="form-control" placeholder="Roll No" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} />
                    <input className="form-control" placeholder="Subject" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
                    <input className="form-control" placeholder="Marks" value={form.marks} onChange={(e) => setForm({ ...form, marks: e.target.value })} />
                    <button className="btn btn-dark" onClick={addMarks}>Save Marks</button>
                </div>
            </DataCard>
            <DataCard title="Marks Register" subtitle="Paginated subject mark entries.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>ID</th><th>Roll No</th><th>Subject</th><th>Marks</th></tr></thead>
                        <tbody>
                            {rows.length ? rows.map((row) => (
                                <tr key={row.id}>
                                    <td>{row.id}</td>
                                    <td><span className="table-chip">{row.roll_no}</span></td>
                                    <td>{row.subject}</td>
                                    <td>{row.marks}</td>
                                </tr>
                            )) : <tr><td colSpan="4"><EmptyState message="No marks data available for the current search." /></td></tr>}
                        </tbody>
                    </table>
                </div>
                <Pagination pagination={pagination} onPage={setPage} />
            </DataCard>
        </div>
    );
}

function DashboardView({ token, notify, setLoading }) {
    const [data, setData] = useState({ students: 0, attendance: 0, marks: 0, top_performers: [], at_risk_students: [] });

    useEffect(() => {
        setLoading(true);
        apiRequest("/api/dashboard", {}, token)
            .then((res) => setData(res))
            .catch((err) => notify(err.message, "error", "Dashboard"))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="page-grid">
            <PageHeader eyebrow="Command Center" title="Academic performance overview" description="A professional snapshot of activity, high performers, and intervention candidates." />
            <div className="metrics-grid metrics-grid-hero">
                <MetricCard label="Students" value={data.students} tone="blue" detail="Registered student profiles" />
                <MetricCard label="Attendance Rows" value={data.attendance} tone="emerald" detail="Tracked attendance entries" />
                <MetricCard label="Marks Rows" value={data.marks} tone="amber" detail="Recorded evaluations" />
            </div>
            <div className="split-grid">
                <DataCard title="Top Performers" subtitle="Students leading the current academic snapshot.">
                    {(data.top_performers || []).length ? data.top_performers.map((item) => (
                        <div className="list-row" key={item.roll_no}>
                            <div><strong>{item.name}</strong><span>Roll {item.roll_no}</span></div>
                            <span className="score-badge">{item.avg_marks}</span>
                        </div>
                    )) : <EmptyState message="No top performer data available." />}
                </DataCard>
                <DataCard title="At-Risk Students" subtitle="Students requiring attention due to marks or attendance.">
                    {(data.at_risk_students || []).length ? data.at_risk_students.map((item) => (
                        <div className="list-row" key={item.roll_no}>
                            <div><strong>{item.name}</strong><span>Roll {item.roll_no}</span></div>
                            <span className="risk-badge">{(item.risk_flags || []).join(", ")}</span>
                        </div>
                    )) : <EmptyState message="No at-risk students identified." />}
                </DataCard>
            </div>
        </div>
    );
}

function ReportsView({ token, notify, setLoading }) {
    const [data, setData] = useState({ total_students: 0, total_at_risk: 0, avg_attendance: 0, avg_marks: 0, department_rows: [], subject_rows: [] });

    useEffect(() => {
        setLoading(true);
        apiRequest("/api/reports", {}, token)
            .then((res) => setData(res))
            .catch((err) => notify(err.message, "error", "Reports"))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="page-grid">
            <PageHeader eyebrow="Reports" title="Department and subject intelligence" description="Use presentation-ready analytics to explain patterns and risk distribution." />
            <div className="metrics-grid">
                <MetricCard label="Students" value={data.total_students} tone="blue" />
                <MetricCard label="At Risk" value={data.total_at_risk} tone="rose" />
                <MetricCard label="Average Attendance" value={`${data.avg_attendance}%`} tone="emerald" />
                <MetricCard label="Average Marks" value={data.avg_marks} tone="amber" />
            </div>
            <DataCard title="Department Analytics" subtitle="Cross-department academic view.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>Department</th><th>Students</th><th>Avg Attendance</th><th>Avg Marks</th><th>At Risk</th></tr></thead>
                        <tbody>
                            {(data.department_rows || []).length ? data.department_rows.map((row) => (
                                <tr key={row.dept}>
                                    <td>{row.dept}</td>
                                    <td>{row.students}</td>
                                    <td>{row.avg_attendance}%</td>
                                    <td>{row.avg_marks}</td>
                                    <td><span className="risk-badge">{row.at_risk_count}</span></td>
                                </tr>
                            )) : <tr><td colSpan="5"><EmptyState message="No department analytics available." /></td></tr>}
                        </tbody>
                    </table>
                </div>
            </DataCard>
            <DataCard title="Subject Analytics" subtitle="Performance spread by subject.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>Subject</th><th>Entries</th><th>Average</th><th>Max</th><th>Min</th></tr></thead>
                        <tbody>
                            {(data.subject_rows || []).length ? data.subject_rows.map((row) => (
                                <tr key={row.subject}>
                                    <td>{row.subject}</td>
                                    <td>{row.entries}</td>
                                    <td>{row.avg_score}</td>
                                    <td>{row.max_score}</td>
                                    <td>{row.min_score}</td>
                                </tr>
                            )) : <tr><td colSpan="5"><EmptyState message="No subject analytics available." /></td></tr>}
                        </tbody>
                    </table>
                </div>
            </DataCard>
        </div>
    );
}

const LazyDashboardView = React.lazy(() => Promise.resolve({ default: DashboardView }));
const LazyStudentsView = React.lazy(() => Promise.resolve({ default: StudentsView }));
const LazyAttendanceView = React.lazy(() => Promise.resolve({ default: AttendanceView }));
const LazyMarksView = React.lazy(() => Promise.resolve({ default: MarksView }));
const LazyReportsView = React.lazy(() => Promise.resolve({ default: ReportsView }));

function AppShell({ route, token, setToken, user, setUser, notify }) {
    const [loading, setLoading] = useState(false);
    const [currentRoute, setCurrentRoute] = useState(route === "login" ? "dashboard" : route);
    const navItems = useMemo(() => ([
        ["dashboard", "Dashboard", "Overview and key insights"],
        ["students", "Students", "Academic roster management"],
        ["attendance", "Attendance", "Presence and risk tracking"],
        ["marks", "Marks", "Scores and evaluations"],
        ["reports", "Reports", "Presentation-ready analytics"]
    ]), []);

    function go(next) {
        setCurrentRoute(next);
        window.history.replaceState({}, "", next === "dashboard" ? "/dashboard" : `/${next}`);
    }

    function logout() {
        setLoading(true);
        apiRequest("/api/logout", { method: "POST" }, token)
            .catch(() => null)
            .finally(() => {
                setToken("");
                setUser("");
                localStorage.removeItem(TOKEN_KEY);
                localStorage.removeItem(USER_KEY);
                window.history.replaceState({}, "", "/login");
                setLoading(false);
            });
    }

    const routeNode = currentRoute === "students"
        ? <LazyStudentsView token={token} notify={notify} setLoading={setLoading} />
        : currentRoute === "attendance"
            ? <LazyAttendanceView token={token} notify={notify} setLoading={setLoading} />
            : currentRoute === "marks"
                ? <LazyMarksView token={token} notify={notify} setLoading={setLoading} />
                : currentRoute === "reports"
                    ? <LazyReportsView token={token} notify={notify} setLoading={setLoading} />
                    : <LazyDashboardView token={token} notify={notify} setLoading={setLoading} />;

    return (
        <div className="app-shell">
            <Loader show={loading} />
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <img className="brand-logo" src="/frontend/assets/logo-mark.svg" alt="logo" />
                    <div><strong>Faculty Analytics</strong><span>Institution Control Panel</span></div>
                </div>
                <div className="user-badge">
                    <span className="user-dot"></span>
                    <div><strong>{user}</strong><small>Faculty session active</small></div>
                </div>
                <nav className="nav-stack">
                    {navItems.map(([id, label, meta]) => (
                        <a key={id} className={`nav-item ${currentRoute === id ? "active" : ""}`} href="#" onClick={(e) => { e.preventDefault(); go(id); }}>
                            <strong>{label}</strong>
                            <span>{meta}</span>
                        </a>
                    ))}
                </nav>
                <button className="btn btn-outline-light sidebar-logout" onClick={logout}>Logout</button>
            </aside>
            <main className="main-area">
                <header className="topbar">
                    <div><span className="topbar-kicker">Live Workspace</span><h1>{navItems.find((item) => item[0] === currentRoute)?.[1] || "Dashboard"}</h1></div>
                    <div className="topbar-pill">Render-ready academic management</div>
                </header>
                <React.Suspense fallback={<div className="panel-card p-3">Loading module...</div>}>{routeNode}</React.Suspense>
            </main>
        </div>
    );
}

function App() {
    const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || "");
    const [user, setUser] = useState(localStorage.getItem(USER_KEY) || "");
    const [route] = useState(getRouteFromPath());
    const [loading, setLoading] = useState(false);
    const [toasts, setToasts] = useState([]);

    function notify(message, type = "info", title = "System") {
        const id = `${Date.now()}-${Math.random()}`;
        setToasts((prev) => [...prev, { id, title, message, type }]);
        setTimeout(() => setToasts((prev) => prev.filter((item) => item.id !== id)), 2800);
    }

    function onLogin(payload) {
        setLoading(true);
        apiRequest("/api/login", { method: "POST", body: JSON.stringify(payload) })
            .then((data) => {
                setToken(data.token);
                setUser(data.user);
                localStorage.setItem(TOKEN_KEY, data.token);
                localStorage.setItem(USER_KEY, data.user);
                notify("Login successful. Workspace is ready.", "success", "Authentication");
                window.history.replaceState({}, "", "/dashboard");
            })
            .catch((err) => notify(err.message, "error", "Authentication"))
            .finally(() => setLoading(false));
    }

    return (
        <>
            <Loader show={loading} />
            <Toasts toasts={toasts} onRemove={(id) => setToasts((prev) => prev.filter((item) => item.id !== id))} />
            {!token ? <LoginView onLogin={onLogin} loading={loading} /> : <AppShell route={route} token={token} setToken={setToken} user={user} setUser={setUser} notify={notify} />}
        </>
    );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
