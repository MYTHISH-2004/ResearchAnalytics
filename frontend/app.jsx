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
            const message = data?.error || data?.message || "Request failed";
            throw new Error(message);
        }
        return data;
    });
}

function Toasts({ toasts, onRemove }) {
    return (
        <div className="toast-stack">
            {toasts.map((toast) => (
                <div key={toast.id} className={`toast-item toast-${toast.type}`}>
                    <span>{toast.message}</span>
                    <button onClick={() => onRemove(toast.id)} className="btn btn-sm btn-light">x</button>
                </div>
            ))}
        </div>
    );
}

function Loader({ show }) {
    if (!show) return null;
    return (
        <div className="page-loader">
            <div className="spinner-border text-light" role="status"></div>
            <p className="mt-2 mb-0 text-light fw-semibold">Loading...</p>
        </div>
    );
}

function LoginView({ onLogin, loading }) {
    const [loginMode, setLoginMode] = useState("email");
    const [email, setEmail] = useState("");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    return (
        <div className="login-page">
            <div className="login-shell fade-in-up">
                <div className="panel-left">
                    <img src="/frontend/assets/logo.svg" alt="logo" style={{ width: 170 }} />
                    <h2 className="mt-3 fw-bold">Faculty Analytics</h2>
                    <p className="mb-0 text-white-50">
                        Unified dashboard for student records, attendance intelligence, and marks analysis.
                    </p>
                </div>
                <div className="panel-right">
                    <h4 className="fw-bold">Sign In</h4>
                    <div className="btn-group mt-2 mb-3 w-100">
                        <button
                            className={`btn ${loginMode === "email" ? "btn-primary" : "btn-outline-primary"}`}
                            onClick={() => setLoginMode("email")}
                        >
                            Email
                        </button>
                        <button
                            className={`btn ${loginMode === "username" ? "btn-primary" : "btn-outline-primary"}`}
                            onClick={() => setLoginMode("username")}
                        >
                            Username
                        </button>
                    </div>
                    {loginMode === "email" ? (
                        <input
                            className="form-control mb-2"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    ) : (
                        <input
                            className="form-control mb-2"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    )}
                    <input
                        className="form-control mb-3"
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <button
                        disabled={loading}
                        className="btn btn-dark w-100 fw-semibold"
                        onClick={() => onLogin({ login_mode: loginMode, email, username, password })}
                    >
                        {loading ? "Signing in..." : "Login"}
                    </button>
                </div>
            </div>
        </div>
    );
}

function Pagination({ pagination, onPage }) {
    if (!pagination) return null;
    const { page, total_pages } = pagination;
    return (
        <div className="d-flex align-items-center justify-content-between mt-3">
            <small className="text-secondary">Page {page} of {total_pages}</small>
            <div className="btn-group">
                <button className="btn btn-sm btn-outline-secondary" disabled={page <= 1} onClick={() => onPage(page - 1)}>
                    Previous
                </button>
                <button
                    className="btn btn-sm btn-outline-secondary"
                    disabled={page >= total_pages}
                    onClick={() => onPage(page + 1)}
                >
                    Next
                </button>
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

    const loadData = () => {
        setLoading(true);
        apiRequest(`/api/students?q=${encodeURIComponent(q)}&dept=${encodeURIComponent(dept)}&page=${page}&per_page=8`, {}, token)
            .then((data) => {
                setRows(data.students || []);
                setDepartments(data.departments || []);
                setPagination(data.pagination);
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadData(); }, [q, dept, page]);

    const addStudent = () => {
        setLoading(true);
        apiRequest("/api/students", { method: "POST", body: JSON.stringify(form) }, token)
            .then(() => {
                notify("Student added", "success");
                setForm({ roll: "", name: "", dept: "" });
                loadData();
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    return (
        <div className="panel-card p-3 fade-in-up">
            <div className="d-flex flex-wrap gap-2 align-items-end">
                <div>
                    <label className="form-label mb-1">Search</label>
                    <input className="form-control" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
                </div>
                <div>
                    <label className="form-label mb-1">Department</label>
                    <select className="form-select" value={dept} onChange={(e) => { setPage(1); setDept(e.target.value); }}>
                        <option value="">All</option>
                        {departments.map((d) => <option key={d} value={d}>{d}</option>)}
                    </select>
                </div>
            </div>
            <hr />
            <div className="row g-2">
                <div className="col-md-2"><input className="form-control" placeholder="Roll" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} /></div>
                <div className="col-md-5"><input className="form-control" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
                <div className="col-md-3"><input className="form-control" placeholder="Dept" value={form.dept} onChange={(e) => setForm({ ...form, dept: e.target.value })} /></div>
                <div className="col-md-2 d-grid"><button className="btn btn-primary" onClick={addStudent}>Add</button></div>
            </div>
            <div className="table-responsive mt-3">
                <table className="table align-middle">
                    <thead><tr><th>Roll</th><th>Name</th><th>Dept</th></tr></thead>
                    <tbody>
                        {rows.map((row) => (
                            <tr key={row.roll_no}>
                                <td>{row.roll_no}</td>
                                <td>{row.name}</td>
                                <td>{row.dept}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <Pagination pagination={pagination} onPage={setPage} />
        </div>
    );
}

function AttendanceView({ token, notify, setLoading }) {
    const [rows, setRows] = useState([]);
    const [page, setPage] = useState(1);
    const [pagination, setPagination] = useState(null);
    const [summary, setSummary] = useState({ overall_percentage: 0, low_attendance_count: 0 });
    const [form, setForm] = useState({ roll: "", total: "", present: "" });

    const loadData = () => {
        setLoading(true);
        apiRequest(`/api/attendance?page=${page}&per_page=8`, {}, token)
            .then((data) => {
                setRows(data.data || []);
                setPagination(data.pagination);
                setSummary({
                    overall_percentage: data.overall_percentage || 0,
                    low_attendance_count: data.low_attendance_count || 0
                });
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadData(); }, [page]);

    const addAttendance = () => {
        setLoading(true);
        apiRequest("/api/attendance", { method: "POST", body: JSON.stringify(form) }, token)
            .then(() => {
                notify("Attendance saved", "success");
                setForm({ roll: "", total: "", present: "" });
                loadData();
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    return (
        <div className="panel-card p-3 fade-in-up">
            <div className="d-flex gap-3 flex-wrap">
                <span className="badge text-bg-success">Overall: {summary.overall_percentage}%</span>
                <span className="badge text-bg-danger">Low Attendance: {summary.low_attendance_count}</span>
            </div>
            <div className="row g-2 mt-2">
                <div className="col-md-3"><input className="form-control" placeholder="Roll" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} /></div>
                <div className="col-md-3"><input className="form-control" placeholder="Total" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })} /></div>
                <div className="col-md-3"><input className="form-control" placeholder="Present" value={form.present} onChange={(e) => setForm({ ...form, present: e.target.value })} /></div>
                <div className="col-md-3 d-grid"><button className="btn btn-primary" onClick={addAttendance}>Add</button></div>
            </div>
            <div className="table-responsive mt-3">
                <table className="table">
                    <thead><tr><th>ID</th><th>Roll</th><th>Total</th><th>Present</th><th>%</th></tr></thead>
                    <tbody>{rows.map((r) => <tr key={r.id}><td>{r.id}</td><td>{r.roll_no}</td><td>{r.total}</td><td>{r.present}</td><td>{r.percentage}</td></tr>)}</tbody>
                </table>
            </div>
            <Pagination pagination={pagination} onPage={setPage} />
        </div>
    );
}

function MarksView({ token, notify, setLoading }) {
    const [rows, setRows] = useState([]);
    const [q, setQ] = useState("");
    const [page, setPage] = useState(1);
    const [pagination, setPagination] = useState(null);
    const [stats, setStats] = useState({ avg_marks: 0, high_scorers: 0, subject_count: 0 });
    const [form, setForm] = useState({ roll: "", subject: "", marks: "" });

    const loadData = () => {
        setLoading(true);
        apiRequest(`/api/marks?q=${encodeURIComponent(q)}&page=${page}&per_page=8`, {}, token)
            .then((data) => {
                setRows(data.data || []);
                setPagination(data.pagination);
                setStats({
                    avg_marks: data.avg_marks || 0,
                    high_scorers: data.high_scorers || 0,
                    subject_count: data.subject_count || 0
                });
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadData(); }, [q, page]);

    const addMarks = () => {
        setLoading(true);
        apiRequest("/api/marks", { method: "POST", body: JSON.stringify(form) }, token)
            .then(() => {
                notify("Marks saved", "success");
                setForm({ roll: "", subject: "", marks: "" });
                loadData();
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    return (
        <div className="panel-card p-3 fade-in-up">
            <div className="d-flex gap-3 flex-wrap mb-2">
                <span className="badge text-bg-primary">Average: {stats.avg_marks}</span>
                <span className="badge text-bg-success">90+: {stats.high_scorers}</span>
                <span className="badge text-bg-warning">Subjects: {stats.subject_count}</span>
            </div>
            <div className="row g-2">
                <div className="col-md-4"><input className="form-control" placeholder="Search by roll/subject" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} /></div>
                <div className="col-md-2"><input className="form-control" placeholder="Roll" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} /></div>
                <div className="col-md-3"><input className="form-control" placeholder="Subject" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} /></div>
                <div className="col-md-2"><input className="form-control" placeholder="Marks" value={form.marks} onChange={(e) => setForm({ ...form, marks: e.target.value })} /></div>
                <div className="col-md-1 d-grid"><button className="btn btn-primary" onClick={addMarks}>Add</button></div>
            </div>
            <div className="table-responsive mt-3">
                <table className="table">
                    <thead><tr><th>ID</th><th>Roll</th><th>Subject</th><th>Marks</th></tr></thead>
                    <tbody>{rows.map((r) => <tr key={r.id}><td>{r.id}</td><td>{r.roll_no}</td><td>{r.subject}</td><td>{r.marks}</td></tr>)}</tbody>
                </table>
            </div>
            <Pagination pagination={pagination} onPage={setPage} />
        </div>
    );
}

function DashboardView({ token, notify, setLoading }) {
    const [data, setData] = useState({ students: 0, attendance: 0, marks: 0, top_performers: [], at_risk_students: [] });

    useEffect(() => {
        setLoading(true);
        apiRequest("/api/dashboard", {}, token)
            .then((res) => setData(res))
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="row g-3 fade-in-up">
            <div className="col-md-4"><div className="panel-card p-3"><small>Total Students</small><h3>{data.students}</h3></div></div>
            <div className="col-md-4"><div className="panel-card p-3"><small>Attendance Rows</small><h3>{data.attendance}</h3></div></div>
            <div className="col-md-4"><div className="panel-card p-3"><small>Marks Rows</small><h3>{data.marks}</h3></div></div>
            <div className="col-md-6">
                <div className="panel-card p-3 h-100">
                    <h6 className="fw-bold">Top Performers</h6>
                    <ul className="mb-0">{(data.top_performers || []).map((s) => <li key={s.roll_no}>{s.name} ({s.avg_marks})</li>)}</ul>
                </div>
            </div>
            <div className="col-md-6">
                <div className="panel-card p-3 h-100">
                    <h6 className="fw-bold">At Risk</h6>
                    <ul className="mb-0">{(data.at_risk_students || []).map((s) => <li key={s.roll_no}>{s.name} ({s.risk_flags.join(", ")})</li>)}</ul>
                </div>
            </div>
        </div>
    );
}

function ReportsView({ token, notify, setLoading }) {
    const [data, setData] = useState({
        total_students: 0, total_at_risk: 0, avg_attendance: 0, avg_marks: 0,
        department_rows: [], subject_rows: []
    });

    useEffect(() => {
        setLoading(true);
        apiRequest("/api/reports", {}, token)
            .then((res) => setData(res))
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="fade-in-up">
            <div className="row g-3 mb-3">
                <div className="col-md-3"><div className="panel-card p-3"><small>Students</small><h4>{data.total_students}</h4></div></div>
                <div className="col-md-3"><div className="panel-card p-3"><small>At Risk</small><h4>{data.total_at_risk}</h4></div></div>
                <div className="col-md-3"><div className="panel-card p-3"><small>Avg Attendance</small><h4>{data.avg_attendance}%</h4></div></div>
                <div className="col-md-3"><div className="panel-card p-3"><small>Avg Marks</small><h4>{data.avg_marks}</h4></div></div>
            </div>
            <div className="panel-card p-3 mb-3">
                <h6 className="fw-bold">Department Analytics</h6>
                <div className="table-responsive">
                    <table className="table">
                        <thead><tr><th>Dept</th><th>Students</th><th>Avg Attendance</th><th>Avg Marks</th><th>At Risk</th></tr></thead>
                        <tbody>{(data.department_rows || []).map((r) => <tr key={r.dept}><td>{r.dept}</td><td>{r.students}</td><td>{r.avg_attendance}</td><td>{r.avg_marks}</td><td>{r.at_risk_count}</td></tr>)}</tbody>
                    </table>
                </div>
            </div>
            <div className="panel-card p-3">
                <h6 className="fw-bold">Subject Analytics</h6>
                <div className="table-responsive">
                    <table className="table">
                        <thead><tr><th>Subject</th><th>Entries</th><th>Avg</th><th>Max</th><th>Min</th></tr></thead>
                        <tbody>{(data.subject_rows || []).map((r) => <tr key={r.subject}><td>{r.subject}</td><td>{r.entries}</td><td>{r.avg_score}</td><td>{r.max_score}</td><td>{r.min_score}</td></tr>)}</tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

// Route-level lazy wrappers for dashboard modules.
const LazyDashboardView = React.lazy(() => Promise.resolve({ default: DashboardView }));
const LazyStudentsView = React.lazy(() => Promise.resolve({ default: StudentsView }));
const LazyAttendanceView = React.lazy(() => Promise.resolve({ default: AttendanceView }));
const LazyMarksView = React.lazy(() => Promise.resolve({ default: MarksView }));
const LazyReportsView = React.lazy(() => Promise.resolve({ default: ReportsView }));

function AppShell({ route, token, setToken, user, setUser, notify }) {
    const [loading, setLoading] = useState(false);
    const [currentRoute, setCurrentRoute] = useState(route === "login" ? "dashboard" : route);

    const navItems = useMemo(() => ([
        ["dashboard", "Dashboard"],
        ["students", "Students"],
        ["attendance", "Attendance"],
        ["marks", "Marks"],
        ["reports", "Reports"]
    ]), []);

    const go = (next) => {
        setCurrentRoute(next);
        const target = next === "dashboard" ? "/dashboard" : `/${next}`;
        window.history.replaceState({}, "", target);
    };

    const logout = () => {
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
    };

    const routeNode = (() => {
        if (currentRoute === "students") return <LazyStudentsView token={token} notify={notify} setLoading={setLoading} />;
        if (currentRoute === "attendance") return <LazyAttendanceView token={token} notify={notify} setLoading={setLoading} />;
        if (currentRoute === "marks") return <LazyMarksView token={token} notify={notify} setLoading={setLoading} />;
        if (currentRoute === "reports") return <LazyReportsView token={token} notify={notify} setLoading={setLoading} />;
        return <LazyDashboardView token={token} notify={notify} setLoading={setLoading} />;
    })();

    return (
        <div className="container-fluid app-shell">
            <Loader show={loading} />
            <div className="row">
                <aside className="col-lg-2 col-md-3 sidebar">
                    <img className="brand-logo" src="/frontend/assets/logo-mark.svg" alt="logo" />
                    <h6 className="fw-bold">Faculty Analytics</h6>
                    <small className="text-white-50 d-block mb-3">{user}</small>
                    <nav className="nav flex-column gap-1">
                        {navItems.map(([id, label]) => (
                            <a
                                key={id}
                                className={`nav-link ${currentRoute === id ? "active" : ""}`}
                                href="#"
                                onClick={(e) => { e.preventDefault(); go(id); }}
                            >
                                {label}
                            </a>
                        ))}
                    </nav>
                    <button className="btn btn-outline-light btn-sm mt-3" onClick={logout}>Logout</button>
                </aside>
                <main className="col-lg-10 col-md-9 content-area">
                    <React.Suspense fallback={<div className="panel-card p-3">Loading module...</div>}>
                        {routeNode}
                    </React.Suspense>
                </main>
            </div>
        </div>
    );
}

function App() {
    const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || "");
    const [user, setUser] = useState(localStorage.getItem(USER_KEY) || "");
    const [route] = useState(getRouteFromPath());
    const [loading, setLoading] = useState(false);
    const [toasts, setToasts] = useState([]);

    const notify = (message, type = "info") => {
        const id = `${Date.now()}-${Math.random()}`;
        setToasts((prev) => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts((prev) => prev.filter((toast) => toast.id !== id));
        }, 2600);
    };

    const onLogin = (payload) => {
        setLoading(true);
        apiRequest("/api/login", { method: "POST", body: JSON.stringify(payload) })
            .then((data) => {
                setToken(data.token);
                setUser(data.user);
                localStorage.setItem(TOKEN_KEY, data.token);
                localStorage.setItem(USER_KEY, data.user);
                notify("Login successful", "success");
                window.history.replaceState({}, "", "/dashboard");
            })
            .catch((err) => notify(err.message, "error"))
            .finally(() => setLoading(false));
    };

    return (
        <>
            <Loader show={loading} />
            <Toasts toasts={toasts} onRemove={(id) => setToasts((prev) => prev.filter((x) => x.id !== id))} />
            {!token ? (
                <LoginView onLogin={onLogin} loading={loading} />
            ) : (
                <AppShell route={route} token={token} setToken={setToken} user={user} setUser={setUser} notify={notify} />
            )}
        </>
    );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
