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

function ActionButtons({ onEdit, onDelete }) {
    return (
        <div className="action-group">
            {onEdit ? <button type="button" className="btn btn-sm btn-outline-secondary action-btn" onClick={onEdit}>Edit</button> : null}
            {onDelete ? <button type="button" className="btn btn-sm btn-outline-danger action-btn" onClick={onDelete}>Delete</button> : null}
        </div>
    );
}

function StudentProfileModal({ student, onClose }) {
    if (!student) return null;
    const riskFlags = student.risk_flags || [];
    const subjectScores = student.subject_scores || [];
    const attendanceHistory = student.attendance_history || [];

    return (
        <div className="profile-modal-backdrop" onClick={onClose}>
            <div className="profile-modal panel-card fade-in-up" onClick={(e) => e.stopPropagation()}>
                <div className="profile-modal-head">
                    <div className="profile-identity">
                        <div className="profile-avatar">
                            <img src="/frontend/assets/logo-mark.svg" alt="Student profile" />
                        </div>
                        <div>
                            <h3>{student.name}</h3>
                            <p>Roll No {student.roll_no} • {student.dept}</p>
                        </div>
                    </div>
                    <button type="button" className="profile-close" onClick={onClose}>Close</button>
                </div>
                <div className="profile-summary">
                    <div className="profile-stat">
                        <span>Attendance</span>
                        <strong>{student.attendance_pct}%</strong>
                    </div>
                    <div className="profile-stat">
                        <span>Average Marks</span>
                        <strong>{student.avg_marks}</strong>
                    </div>
                    <div className="profile-stat">
                        <span>Classes Present</span>
                        <strong>{student.total_present}/{student.total_classes}</strong>
                    </div>
                </div>
                <div className="profile-grid">
                    <div className="profile-section">
                        <div className="profile-section-head">
                            <h4>Risk Overview</h4>
                            <span>{riskFlags.length ? "Intervention required" : "No active risk"}</span>
                        </div>
                        <div className="profile-badge-row">
                            {riskFlags.length
                                ? riskFlags.map((flag) => <span key={flag} className="status-badge status-risk">{flag}</span>)
                                : <span className="status-badge status-active">Stable Profile</span>}
                        </div>
                    </div>
                    <div className="profile-section">
                        <div className="profile-section-head">
                            <h4>Marks History</h4>
                            <span>{subjectScores.length} recorded subjects</span>
                        </div>
                        {subjectScores.length ? (
                            <div className="mini-table">
                                {subjectScores.map((item, index) => (
                                    <div key={`${item.subject}-${index}`} className="mini-row">
                                        <span>{item.subject}</span>
                                        <strong>{item.marks}</strong>
                                    </div>
                                ))}
                            </div>
                        ) : <EmptyState message="No marks recorded for this student." />}
                    </div>
                    <div className="profile-section">
                        <div className="profile-section-head">
                            <h4>Attendance History</h4>
                            <span>{attendanceHistory.length} attendance entries</span>
                        </div>
                        {attendanceHistory.length ? (
                            <div className="mini-table">
                                {attendanceHistory.map((item) => (
                                    <div key={item.id} className="mini-row mini-row-wide">
                                        <span>ID {item.id} • {item.present}/{item.total} classes</span>
                                        <strong>{item.percentage}%</strong>
                                    </div>
                                ))}
                            </div>
                        ) : <EmptyState message="No attendance recorded for this student." />}
                    </div>
                </div>
            </div>
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
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [editingRoll, setEditingRoll] = useState(null);

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

    function saveStudent() {
        setLoading(true);
        const isEditing = Boolean(editingRoll);
        const path = isEditing ? `/api/students/${editingRoll}` : "/api/students";
        const method = isEditing ? "PUT" : "POST";
        apiRequest(path, { method, body: JSON.stringify(form) }, token)
            .then(() => {
                notify(isEditing ? "Student record updated successfully." : "Student record created successfully.", "success", "Students");
                setForm({ roll: "", name: "", dept: "" });
                setEditingRoll(null);
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Students"))
            .finally(() => setLoading(false));
    }

    function editStudent(row) {
        setEditingRoll(row.roll_no);
        setForm({ roll: String(row.roll_no), name: row.name, dept: row.dept });
    }

    function deleteStudent(rollNo) {
        if (!window.confirm(`Delete student ${rollNo}?`)) return;
        setLoading(true);
        apiRequest(`/api/students/${rollNo}`, { method: "DELETE" }, token)
            .then(() => {
                notify("Student record deleted successfully.", "success", "Students");
                if (editingRoll === rollNo) {
                    setEditingRoll(null);
                    setForm({ roll: "", name: "", dept: "" });
                }
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Students"))
            .finally(() => setLoading(false));
    }

    function openStudentProfile(rollNo) {
        setLoading(true);
        apiRequest(`/api/students/${rollNo}/profile`, {}, token)
            .then((data) => setSelectedStudent(data.student || null))
            .catch((err) => notify(err.message, "error", "Student Profile"))
            .finally(() => setLoading(false));
    }

    const visibleCount = rows.length;
    const totalStudents = pagination?.total || visibleCount;

    return (
        <div className="page-grid">
            <StudentProfileModal student={selectedStudent} onClose={() => setSelectedStudent(null)} />
            <PageHeader eyebrow="Student Directory" title="Manage student records" description="Search departments, add new learners, and keep the academic roster clean." />
            <div className="insight-strip">
                <div className="insight-tile">
                    <span className="insight-label">Total Directory Size</span>
                    <strong>{totalStudents}</strong>
                    <small>Managed student profiles</small>
                </div>
                <div className="insight-tile">
                    <span className="insight-label">Departments</span>
                    <strong>{departments.length || 0}</strong>
                    <small>Distinct academic units</small>
                </div>
                <div className="insight-tile">
                    <span className="insight-label">Current View</span>
                    <strong>{visibleCount}</strong>
                    <small>{dept || "All departments"} filtered results</small>
                </div>
            </div>
            <div className="split-grid split-grid-feature">
                <DataCard title="Directory Controls" subtitle="Search and refine the active student roster.">
                    <div className="control-grid">
                        <label className="field-block">
                            <span>Search by name or roll</span>
                            <input className="form-control" placeholder="Search roster" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
                        </label>
                        <label className="field-block">
                            <span>Department</span>
                            <select className="form-select" value={dept} onChange={(e) => { setPage(1); setDept(e.target.value); }}>
                                <option value="">All Departments</option>
                                {departments.map((item) => <option key={item} value={item}>{item}</option>)}
                            </select>
                        </label>
                    </div>
                    <div className="section-note">Use the filter set to isolate a department or locate a profile quickly during review meetings.</div>
                </DataCard>
                <DataCard title={editingRoll ? "Edit Student" : "Add New Student"} subtitle={editingRoll ? "Update the selected student record." : "Register a new learner in the academic system."}>
                    <div className="entry-stack">
                        <input className="form-control" placeholder="Roll No" disabled={Boolean(editingRoll)} value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} />
                        <input className="form-control" placeholder="Student Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                        <input className="form-control" placeholder="Department" value={form.dept} onChange={(e) => setForm({ ...form, dept: e.target.value })} />
                        <div className="action-row">
                            <button className="btn btn-dark btn-wide" onClick={saveStudent}>{editingRoll ? "Update Student" : "Add Student"}</button>
                            {editingRoll ? <button type="button" className="btn btn-outline-secondary btn-wide" onClick={() => { setEditingRoll(null); setForm({ roll: "", name: "", dept: "" }); }}>Cancel</button> : null}
                        </div>
                    </div>
                </DataCard>
            </div>
            <DataCard title="Student Records" subtitle="Current roster across departments with identity and ownership details.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>Profile</th><th>Student Identity</th><th>Department</th><th>Status</th><th>Actions</th></tr></thead>
                        <tbody>
                            {rows.length ? rows.map((row) => (
                                <tr key={row.roll_no}>
                                    <td>
                                        <div className="student-profile">
                                            <button type="button" className="student-avatar-button" onClick={() => openStudentProfile(row.roll_no)}>
                                                <div className="student-avatar">
                                                <img src="/frontend/assets/logo-mark.svg" alt="Student profile" />
                                                </div>
                                            </button>
                                        </div>
                                    </td>
                                    <td>
                                        <button type="button" className="entity-button" onClick={() => openStudentProfile(row.roll_no)}>
                                            <div className="entity-main">
                                            <strong>{row.name}</strong>
                                            <span>Roll No {row.roll_no}</span>
                                            </div>
                                        </button>
                                    </td>
                                    <td><span className="neutral-badge">{row.dept}</span></td>
                                    <td><span className="status-badge status-active">Active Record</span></td>
                                    <td><ActionButtons onEdit={() => editStudent(row)} onDelete={() => deleteStudent(row.roll_no)} /></td>
                                </tr>
                            )) : <tr><td colSpan="5"><EmptyState message="No student records match the current filter." /></td></tr>}
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
    const [editingId, setEditingId] = useState(null);

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

    function saveAttendance() {
        setLoading(true);
        const path = editingId ? `/api/attendance/${editingId}` : "/api/attendance";
        const method = editingId ? "PUT" : "POST";
        apiRequest(path, { method, body: JSON.stringify(form) }, token)
            .then(() => {
                notify(editingId ? "Attendance record updated successfully." : "Attendance record saved successfully.", "success", "Attendance");
                setForm({ roll: "", total: "", present: "" });
                setEditingId(null);
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Attendance"))
            .finally(() => setLoading(false));
    }

    function editAttendance(row) {
        setEditingId(row.id);
        setForm({ roll: String(row.roll_no), total: String(row.total), present: String(row.present) });
    }

    function deleteAttendance(id) {
        if (!window.confirm(`Delete attendance row ${id}?`)) return;
        setLoading(true);
        apiRequest(`/api/attendance/${id}`, { method: "DELETE" }, token)
            .then(() => {
                notify("Attendance record deleted successfully.", "success", "Attendance");
                if (editingId === id) {
                    setEditingId(null);
                    setForm({ roll: "", total: "", present: "" });
                }
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
            <div className="split-grid split-grid-feature">
                <DataCard title={editingId ? "Edit Attendance" : "Attendance Intake"} subtitle={editingId ? "Update the selected attendance row." : "Capture the latest attendance values for a student record."}>
                    <div className="entry-stack">
                        <input className="form-control" placeholder="Roll No" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} />
                        <input className="form-control" placeholder="Total Classes" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })} />
                        <input className="form-control" placeholder="Present Classes" value={form.present} onChange={(e) => setForm({ ...form, present: e.target.value })} />
                        <div className="action-row">
                            <button className="btn btn-dark btn-wide" onClick={saveAttendance}>{editingId ? "Update Attendance" : "Save Attendance"}</button>
                            {editingId ? <button type="button" className="btn btn-outline-secondary btn-wide" onClick={() => { setEditingId(null); setForm({ roll: "", total: "", present: "" }); }}>Cancel</button> : null}
                        </div>
                    </div>
                </DataCard>
                <DataCard title="Operational Guidance" subtitle="Use the register to intervene before attendance risk compounds.">
                    <div className="brief-list">
                        <div className="brief-row"><strong>Threshold</strong><span>Students below 75% should be reviewed in the next faculty cycle.</span></div>
                        <div className="brief-row"><strong>Refresh Cadence</strong><span>Update the register after each assessment block or class cycle.</span></div>
                        <div className="brief-row"><strong>Review View</strong><span>Paginated records help track low-attendance patterns over time.</span></div>
                    </div>
                </DataCard>
            </div>
            <DataCard title="Attendance Register" subtitle="Paginated attendance history with participation status.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>Record</th><th>Academic Load</th><th>Present</th><th>Percentage</th><th>Risk State</th><th>Actions</th></tr></thead>
                        <tbody>
                            {rows.length ? rows.map((row) => (
                                <tr key={row.id}>
                                    <td>
                                        <div className="entity-main">
                                            <strong>Roll No {row.roll_no}</strong>
                                            <span>Attendance ID {row.id}</span>
                                        </div>
                                    </td>
                                    <td>{row.total} classes</td>
                                    <td><span className="table-chip">{row.present}</span></td>
                                    <td>{row.percentage}%</td>
                                    <td><span className={`status-badge ${Number(row.percentage) < 75 ? "status-risk" : "status-active"}`}>{Number(row.percentage) < 75 ? "Needs Review" : "On Track"}</span></td>
                                    <td><ActionButtons onEdit={() => editAttendance(row)} onDelete={() => deleteAttendance(row.id)} /></td>
                                </tr>
                            )) : <tr><td colSpan="6"><EmptyState message="No attendance entries available yet." /></td></tr>}
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
    const [editingId, setEditingId] = useState(null);

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

    function saveMarks() {
        setLoading(true);
        const path = editingId ? `/api/marks/${editingId}` : "/api/marks";
        const method = editingId ? "PUT" : "POST";
        apiRequest(path, { method, body: JSON.stringify(form) }, token)
            .then(() => {
                notify(editingId ? "Marks updated successfully." : "Marks saved successfully.", "success", "Marks");
                setForm({ roll: "", subject: "", marks: "" });
                setEditingId(null);
                loadData();
            })
            .catch((err) => notify(err.message, "error", "Marks"))
            .finally(() => setLoading(false));
    }

    function editMarks(row) {
        setEditingId(row.id);
        setForm({ roll: String(row.roll_no), subject: row.subject, marks: String(row.marks) });
    }

    function deleteMarks(id) {
        if (!window.confirm(`Delete marks row ${id}?`)) return;
        setLoading(true);
        apiRequest(`/api/marks/${id}`, { method: "DELETE" }, token)
            .then(() => {
                notify("Marks record deleted successfully.", "success", "Marks");
                if (editingId === id) {
                    setEditingId(null);
                    setForm({ roll: "", subject: "", marks: "" });
                }
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
            <div className="split-grid split-grid-feature">
                <DataCard title="Search Ledger" subtitle="Filter the marks register by roll number or subject.">
                    <div className="control-grid control-grid-single">
                        <label className="field-block field-wide">
                            <span>Search by roll or subject</span>
                            <input className="form-control" placeholder="Search marks ledger" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
                        </label>
                    </div>
                    <div className="section-note">The marks register updates in real time as you narrow the academic search context.</div>
                </DataCard>
                <DataCard title={editingId ? "Edit Marks Entry" : "Add Marks Entry"} subtitle={editingId ? "Update the selected score entry." : "Record a fresh score for the selected student and subject."}>
                    <div className="entry-stack">
                        <input className="form-control" placeholder="Roll No" value={form.roll} onChange={(e) => setForm({ ...form, roll: e.target.value })} />
                        <input className="form-control" placeholder="Subject" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
                        <input className="form-control" placeholder="Marks" value={form.marks} onChange={(e) => setForm({ ...form, marks: e.target.value })} />
                        <div className="action-row">
                            <button className="btn btn-dark btn-wide" onClick={saveMarks}>{editingId ? "Update Marks" : "Save Marks"}</button>
                            {editingId ? <button type="button" className="btn btn-outline-secondary btn-wide" onClick={() => { setEditingId(null); setForm({ roll: "", subject: "", marks: "" }); }}>Cancel</button> : null}
                        </div>
                    </div>
                </DataCard>
            </div>
            <DataCard title="Marks Register" subtitle="Paginated subject mark entries with performance classification.">
                <div className="table-shell">
                    <table className="table table-borderless align-middle ui-table">
                        <thead><tr><th>Candidate</th><th>Subject</th><th>Marks</th><th>Performance Band</th><th>Actions</th></tr></thead>
                        <tbody>
                            {rows.length ? rows.map((row) => (
                                <tr key={row.id}>
                                    <td>
                                        <div className="entity-main">
                                            <strong>Roll No {row.roll_no}</strong>
                                            <span>Marks ID {row.id}</span>
                                        </div>
                                    </td>
                                    <td><span className="neutral-badge">{row.subject}</span></td>
                                    <td><span className="table-chip">{row.marks}</span></td>
                                    <td><span className={`status-badge ${Number(row.marks) >= 90 ? "status-active" : Number(row.marks) >= 75 ? "status-watch" : "status-risk"}`}>{Number(row.marks) >= 90 ? "Outstanding" : Number(row.marks) >= 75 ? "Stable" : "Needs Support"}</span></td>
                                    <td><ActionButtons onEdit={() => editMarks(row)} onDelete={() => deleteMarks(row.id)} /></td>
                                </tr>
                            )) : <tr><td colSpan="5"><EmptyState message="No marks data available for the current search." /></td></tr>}
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

    function exportCsv(type) {
        window.open(`/export/${type}`, "_blank", "noopener,noreferrer");
    }

    return (
        <div className="page-grid">
            <PageHeader eyebrow="Reports" title="Department and subject intelligence" description="Use presentation-ready analytics to explain patterns and risk distribution." />
            <div className="metrics-grid">
                <MetricCard label="Students" value={data.total_students} tone="blue" />
                <MetricCard label="At Risk" value={data.total_at_risk} tone="rose" />
                <MetricCard label="Average Attendance" value={`${data.avg_attendance}%`} tone="emerald" />
                <MetricCard label="Average Marks" value={data.avg_marks} tone="amber" />
            </div>
            <DataCard title="Report Actions" subtitle="Download current academic datasets for reporting and archival.">
                <div className="action-row action-row-report">
                    <button type="button" className="btn btn-outline-secondary" onClick={() => exportCsv("students")}>Export Students</button>
                    <button type="button" className="btn btn-outline-secondary" onClick={() => exportCsv("attendance")}>Export Attendance</button>
                    <button type="button" className="btn btn-outline-secondary" onClick={() => exportCsv("marks")}>Export Marks</button>
                </div>
            </DataCard>
            <div className="report-grid">
                <DataCard title="Department Analytics" subtitle="Cross-department academic view with risk concentration.">
                    <div className="table-shell">
                        <table className="table table-borderless align-middle ui-table">
                            <thead><tr><th>Department</th><th>Students</th><th>Avg Attendance</th><th>Avg Marks</th><th>Risk</th></tr></thead>
                            <tbody>
                                {(data.department_rows || []).length ? data.department_rows.map((row) => (
                                    <tr key={row.dept}>
                                        <td>
                                            <div className="entity-main">
                                                <strong>{row.dept}</strong>
                                                <span>Department performance cluster</span>
                                            </div>
                                        </td>
                                        <td>{row.students}</td>
                                        <td>{row.avg_attendance}%</td>
                                        <td>{row.avg_marks}</td>
                                        <td><span className={`status-badge ${row.at_risk_count ? "status-risk" : "status-active"}`}>{row.at_risk_count} flagged</span></td>
                                    </tr>
                                )) : <tr><td colSpan="5"><EmptyState message="No department analytics available." /></td></tr>}
                            </tbody>
                        </table>
                    </div>
                </DataCard>
                <DataCard title="Subject Analytics" subtitle="Performance spread by subject with score range visibility.">
                    <div className="table-shell">
                        <table className="table table-borderless align-middle ui-table">
                            <thead><tr><th>Subject</th><th>Entries</th><th>Average</th><th>Range</th></tr></thead>
                            <tbody>
                                {(data.subject_rows || []).length ? data.subject_rows.map((row) => (
                                    <tr key={row.subject}>
                                        <td>
                                            <div className="entity-main">
                                                <strong>{row.subject}</strong>
                                                <span>Assessment coverage</span>
                                            </div>
                                        </td>
                                        <td>{row.entries}</td>
                                        <td><span className="table-chip">{row.avg_score}</span></td>
                                        <td><span className="neutral-badge">{row.min_score} - {row.max_score}</span></td>
                                    </tr>
                                )) : <tr><td colSpan="4"><EmptyState message="No subject analytics available." /></td></tr>}
                            </tbody>
                        </table>
                    </div>
                </DataCard>
            </div>
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
                    <div className="topbar-pill">Enterprise academic operations</div>
                </header>
                <React.Suspense fallback={<div className="panel-card p-3">Loading module...</div>}>{routeNode}</React.Suspense>
            </main>
        </div>
    );
}

function App() {
    const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || "");
    const [user, setUser] = useState(localStorage.getItem(USER_KEY) || "");
    const [route, setRoute] = useState(getRouteFromPath());
    const [loading, setLoading] = useState(false);
    const [toasts, setToasts] = useState([]);

    useEffect(() => {
        const path = window.location.pathname.toLowerCase();
        if (path === "/" || path === "/login") {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            setToken("");
            setUser("");
            if (path !== "/login") {
                window.history.replaceState({}, "", "/login");
                setRoute("login");
            }
        }
    }, []);

    useEffect(() => {
        const handleNavigation = () => setRoute(getRouteFromPath());
        window.addEventListener("popstate", handleNavigation);
        return () => window.removeEventListener("popstate", handleNavigation);
    }, []);

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
                setRoute("dashboard");
            })
            .catch((err) => notify(err.message, "error", "Authentication"))
            .finally(() => setLoading(false));
    }

    return (
        <>
            <Loader show={loading} />
            <Toasts toasts={toasts} onRemove={(id) => setToasts((prev) => prev.filter((item) => item.id !== id))} />
            {!token || route === "login"
                ? <LoginView onLogin={onLogin} loading={loading} />
                : <AppShell route={route} token={token} setToken={setToken} user={user} setUser={setUser} notify={notify} />}
        </>
    );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
